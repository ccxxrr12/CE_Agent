-- ============================================================================
-- CHEATENGINE MCP 桥接 v11.4 - 强化版
-- ============================================================================
-- 结合基于定时器的管道通信(v10)与完整的命令集(v8)
-- 这是生产版本，包含所有AI驱动逆向工程工具
-- v11.4.0: 添加了启动/停止时的健壮清理以防止僵尸断点/监视
--          确保即使在资源处于活动状态时也能在脚本重载时清理状态
-- v11.3.1: 通用32/64位处理，改进断点捕获，稳健分析
--          修复analyze_function, readPointer用于指针链
-- ============================================================================

local PIPE_NAME = "CE_MCP_Bridge_v99"
local VERSION = "11.4.0"

-- 全局状态
local serverState = {
    running = false,
    timer = nil,
    pipe = nil,
    connected = false,
    scan_memscan = nil,
    scan_foundlist = nil,
    breakpoints = {},
    breakpoint_hits = {},
    hw_bp_slots = {},      -- 硬件断点槽(最多4个)
    active_watches = {}    -- 虚拟机管理程序级跟踪的DBVM监视ID
}

-- ============================================================================
-- 工具函数
-- ============================================================================

-- 将数值转换为十六进制字符串
local function toHex(num)
    if not num then return "nil" end
    -- 正确处理32位和64位地址
    -- Lua数字是双精度，所以我们需要小心处理大整数
    if num < 0 then
        -- 处理负数(有符号解释)
        return string.format("-0x%X", -num)
    elseif num > 0xFFFFFFFF then
        -- 64位地址：使用正确格式
        local high = math.floor(num / 0x100000000)
        local low = num % 0x100000000
        return string.format("0x%X%08X", high, low)
    else
        -- 32位地址
        return string.format("0x%08X", num)
    end
end

-- 日志输出函数
local function log(msg)
    print("[MCP v" .. VERSION .. "] " .. msg)
end

-- 通用32/64位架构助手
-- 返回指针大小、目标是否为64位以及当前堆栈/指令指针
local function getArchInfo()
    local is64 = targetIs64Bit()
    local ptrSize = is64 and 8 or 4
    local stackPtr = is64 and (RSP or ESP) or ESP
    local instPtr = is64 and (RIP or EIP) or EIP
    return {
        is64bit = is64,
        ptrSize = ptrSize,
        stackPtr = stackPtr,
        instPtr = instPtr
    }
end

-- 通用寄存器捕获 - 适用于32位和64位目标
local function captureRegisters()
    local is64 = targetIs64Bit()
    if is64 then
        return {
            RAX = RAX and toHex(RAX) or nil,
            RBX = RBX and toHex(RBX) or nil,
            RCX = RCX and toHex(RCX) or nil,
            RDX = RDX and toHex(RDX) or nil,
            RSI = RSI and toHex(RSI) or nil,
            RDI = RDI and toHex(RDI) or nil,
            RBP = RBP and toHex(RBP) or nil,
            RSP = RSP and toHex(RSP) or nil,
            RIP = RIP and toHex(RIP) or nil,
            R8 = R8 and toHex(R8) or nil,
            R9 = R9 and toHex(R9) or nil,
            R10 = R10 and toHex(R10) or nil,
            R11 = R11 and toHex(R11) or nil,
            R12 = R12 and toHex(R12) or nil,
            R13 = R13 and toHex(R13) or nil,
            R14 = R14 and toHex(R14) or nil,
            R15 = R15 and toHex(R15) or nil,
            EFLAGS = EFLAGS and toHex(EFLAGS) or nil,
            arch = "x64"
        }
    else
        return {
            EAX = EAX and toHex(EAX) or nil,
            EBX = EBX and toHex(EBX) or nil,
            ECX = ECX and toHex(ECX) or nil,
            EDX = EDX and toHex(EDX) or nil,
            ESI = ESI and toHex(ESI) or nil,
            EDI = EDI and toHex(EDI) or nil,
            EBP = EBP and toHex(EBP) or nil,
            ESP = ESP and toHex(ESP) or nil,
            EIP = EIP and toHex(EIP) or nil,
            EFLAGS = EFLAGS and toHex(EFLAGS) or nil,
            arch = "x86"
        }
    end
end

-- 通用堆栈捕获 - 使用正确的指针大小读取堆栈
local function captureStack(depth)
    local arch = getArchInfo()
    local stack = {}
    local stackPtr = arch.stackPtr
    if not stackPtr then return stack end
    
    for i = 0, depth - 1 do
        local val
        if arch.is64bit then
            val = readQword(stackPtr + i * arch.ptrSize)
        else
            val = readInteger(stackPtr + i * arch.ptrSize)
        end
        if val then stack[i] = toHex(val) end
    end
    return stack
end

-- ============================================================================
-- 清理与安全例程（对健壮性至关重要）
-- ============================================================================
-- 防止脚本重新加载时出现"僵尸"断点和DBVM监视

local function cleanupZombieState()
    log("正在清理僵尸资源...")
    local cleaned = { breakpoints = 0, dbvm_watches = 0, scans = 0 }
    
    -- 1. 移除所有由我们管理的硬件断点
    if serverState.breakpoints then
        for id, bp in pairs(serverState.breakpoints) do
            if bp.address then
                local ok = pcall(function() debug_removeBreakpoint(bp.address) end)
                if ok then cleaned.breakpoints = cleaned.breakpoints + 1 end
            end
        end
    end
    
    -- 2. 停止所有DBVM监视
    if serverState.active_watches then
        for key, watch in pairs(serverState.active_watches) do
            if watch.id then
                local ok = pcall(function() dbvm_watch_disable(watch.id) end)
                if ok then cleaned.dbvm_watches = cleaned.dbvm_watches + 1 end
            end
        end
    end

    -- 3. 清理扫描内存对象
    if serverState.scan_memscan then
        pcall(function() serverState.scan_memscan.destroy() end)
        serverState.scan_memscan = nil
        cleaned.scans = cleaned.scans + 1
    end
    if serverState.scan_foundlist then
        pcall(function() serverState.scan_foundlist.destroy() end)
        serverState.scan_foundlist = nil
    end

    -- 重置所有跟踪表
    serverState.breakpoints = {}
    serverState.breakpoint_hits = {}
    serverState.hw_bp_slots = {}
    serverState.active_watches = {}
    
    if cleaned.breakpoints > 0 or cleaned.dbvm_watches > 0 or cleaned.scans > 0 then
        log(string.format("已清理: %d 个断点, %d 个DBVM监视, %d 个扫描", 
            cleaned.breakpoints, cleaned.dbvm_watches, cleaned.scans))
    end
    
    return cleaned
end

-- ============================================================================
-- JSON库（纯Lua - 完整实现）
-- ============================================================================
local json = {}
local encode

local escape_char_map = { [ "\\" ] = "\\", [ "\"" ] = "\"", [ "\b" ] = "b", [ "\f" ] = "f", [ "\n" ] = "n", [ "\r" ] = "r", [ "\t" ] = "t" }
local escape_char_map_inv = { [ "/" ] = "/" }
for k, v in pairs(escape_char_map) do escape_char_map_inv[v] = k end
local function escape_char(c) return "\\" .. (escape_char_map[c] or string.format("u%04x", c:byte())) end
local function encode_nil(val) return "null" end
local function encode_table(val, stack)
  local res, stack = {}, stack or {}
  if stack[val] then error("circular reference") end
  stack[val] = true
  if rawget(val, 1) ~= nil or next(val) == nil then
    for i, v in ipairs(val) do table.insert(res, encode(v, stack)) end
    stack[val] = nil
    return "[" .. table.concat(res, ",") .. "]"
  else
    for k, v in pairs(val) do
      if type(k) ~= "string" then k = tostring(k) end
      table.insert(res, encode(k, stack) .. ":" .. encode(v, stack))
    end
    stack[val] = nil
    return "{" .. table.concat(res, ",") .. "}"
  end
end
local function encode_string(val) return '"' .. val:gsub('[%z\1-\31\\"]', escape_char) .. '"' end
local function encode_number(val) if val ~= val or val <= -math.huge or val >= math.huge then return "null" end return string.format("%.14g", val) end
local type_func_map = { ["nil"] = encode_nil, ["table"] = encode_table, ["string"] = encode_string, ["number"] = encode_number, ["boolean"] = tostring, ["function"] = function() return "null" end, ["userdata"] = function() return "null" end }
encode = function(val, stack) local t = type(val) local f = type_func_map[t] if f then return f(val, stack) end error("unexpected type '" .. t .. "'") end
json.encode = encode

local function decode_scanwhite(str, pos) return str:find("%S", pos) or #str + 1 end
local decode
local function decode_string(str, pos)
  local startpos = pos + 1
  local endpos = pos
  while true do
    endpos = str:find('["\\]', endpos + 1)
    if not endpos then return nil, "expected closing quote" end
    if str:sub(endpos, endpos) == '"' then break end
    endpos = endpos + 1
  end
  local s = str:sub(startpos, endpos - 1)
  s = s:gsub("\\.", function(c) return escape_char_map_inv[c:sub(2)] or c end)
  s = s:gsub("\\u(%x%x%x%x)", function(hex) return string.char(tonumber(hex, 16)) end)
  return s, endpos + 1
end
local function decode_number(str, pos)
  local numstr = str:match("^-?%d+%.?%d*[eE]?[+-]?%d*", pos)
  local val = tonumber(numstr)
  if not val then return nil, "invalid number" end
  return val, pos + #numstr
end
local function decode_literal(str, pos)
  local word = str:match("^%a+", pos)
  if word == "true" then return true, pos + 4 end
  if word == "false" then return false, pos + 5 end
  if word == "null" then return nil, pos + 4 end
  return nil, "invalid literal"
end
local function decode_array(str, pos)
  pos = pos + 1
  local arr, n = {}, 0
  pos = decode_scanwhite(str, pos)
  if str:sub(pos, pos) == "]" then return arr, pos + 1 end
  while true do
    local val val, pos = decode(str, pos)
    n = n + 1 arr[n] = val
    pos = decode_scanwhite(str, pos)
    local c = str:sub(pos, pos)
    if c == "]" then return arr, pos + 1 end
    if c ~= "," then return nil, "expected ']' or ','" end
    pos = decode_scanwhite(str, pos + 1)
  end
end
local function decode_object(str, pos)
  pos = pos + 1
  local obj = {}
  pos = decode_scanwhite(str, pos)
  if str:sub(pos, pos) == "}" then return obj, pos + 1 end
  while true do
    local key key, pos = decode_string(str, pos) if not key then return nil, "expected string key" end
    pos = decode_scanwhite(str, pos)
    if str:sub(pos, pos) ~= ":" then return nil, "expected ':'" end
    pos = decode_scanwhite(str, pos + 1)
    local val val, pos = decode(str, pos) obj[key] = val
    pos = decode_scanwhite(str, pos)
    local c = str:sub(pos, pos)
    if c == "}" then return obj, pos + 1 end
    if c ~= "," then return nil, "expected '}' or ','" end
    pos = decode_scanwhite(str, pos + 1)
  end
end
local char_func_map = { ['"'] = decode_string, ["{"] = decode_object, ["["] = decode_array }
setmetatable(char_func_map, { __index = function(t, c) if c:match("%d") or c == "-" then return decode_number end return decode_literal end })
decode = function(str, pos)
  pos = pos or 1
  pos = decode_scanwhite(str, pos)
  local c = str:sub(pos, pos)
  return char_func_map[c](str, pos)
end
json.decode = decode

-- ============================================================================
-- 命令处理程序 - 进程和模块
-- ============================================================================

local function cmd_get_process_info(params)
    -- 强制刷新：告诉CE尝试使用当前DBVM权限重新加载符号
    pcall(reinitializeSymbolhandler)
    
    local pid = getOpenedProcessID()
    if pid and pid > 0 then
        -- 使用与enum_modules相同的逻辑获取模块（带有AOB回退）
        local modules = enumModules(pid)
        if not modules or #modules == 0 then
            modules = enumModules()
        end
        
        -- 构建模块列表
        local moduleList = {}
        local mainModuleName = nil
        local usedAobFallback = false
        
        if modules and #modules > 0 then
            for i = 1, math.min(#modules, 50) do
                local m = modules[i]
                if m then
                    table.insert(moduleList, {
                        name = m.Name or "???",
                        address = toHex(m.Address or 0),
                        size = m.Size or 0
                    })
                    if i == 1 then mainModuleName = m.Name end
                end
            end
        end
        
        -- 如果仍然没有模块，尝试AOB回退来查找PE头并读取导出目录名称
        if #moduleList == 0 then
            usedAobFallback = true
            local mzScan = AOBScan("4D 5A 90 00 03 00 00 00")
            if mzScan and mzScan.Count > 0 then
                for i = 0, math.min(mzScan.Count - 1, 50) do
                    local addr = tonumber(mzScan.getString(i), 16)
                    if addr then
                        local peOffset = readInteger(addr + 0x3C)
                        local moduleSize = 0
                        local realName = nil
                        
                        if peOffset and peOffset > 0 and peOffset < 0x1000 then
                            -- 获取映像大小
                            local sizeOfImage = readInteger(addr + peOffset + 0x50)
                            if sizeOfImage then moduleSize = sizeOfImage end
                            
                            -- 尝试从导出目录读取内部名称
                            -- PE头+0x78是导出数据目录(32位)
                            local exportRVA = readInteger(addr + peOffset + 0x78)
                            if exportRVA and exportRVA > 0 and exportRVA < 0x10000000 then
                                -- 导出目录+0x0C是名称RVA
                                local nameRVA = readInteger(addr + exportRVA + 0x0C)
                                if nameRVA and nameRVA > 0 and nameRVA < 0x10000000 then
                                    local name = readString(addr + nameRVA, 64)
                                    if name and #name > 0 and #name < 60 then
                                        realName = name
                                    end
                                end
                            end
                        end
                        
                        -- 确定模块名称
                        local modName
                        if realName then
                            modName = realName
                        elseif i == 0 then
                            -- 第一个模块可能是主exe - 使用进程名称或L2.exe
                            modName = (process ~= "" and process) or "L2.exe"
                        else
                            modName = "Module_" .. string.format("%X", addr)
                        end
                        
                        table.insert(moduleList, {
                            name = modName,
                            address = toHex(addr),
                            size = moduleSize,
                            source = realName and "export_directory" or "aob_fallback"
                        })
                        
                        if i == 0 then mainModuleName = modName end
                    end
                end
                mzScan.destroy()
            end
        end
        
        -- 如果可用则使用实际进程名称，否则默认为L2.exe
        -- 重要：不要使用AOB扫描的mainModuleName - 它只是按内存顺序排列的第一个DLL
        -- 这可能是任何东西。当反作弊隐藏进程时，我们硬编码L2.exe。
        local name = (process ~= "" and process) or "L2.exe"
        
        return { 
            success = true, 
            process_id = pid, 
            process_name = name,
            module_count = #moduleList,
            modules = moduleList,
            used_aob_fallback = usedAobFallback
        }
    end
    return { success = false, error = "未附加进程" }
end

local function cmd_enum_modules(params)
    local pid = getOpenedProcessID()
    local modules = enumModules(pid)  -- 首先尝试PID
    
    -- 如果失败，尝试不带PID
    if not modules or #modules == 0 then
        modules = enumModules()
    end
    
    local result = {}
    if modules and #modules > 0 then
        for i, m in ipairs(modules) do
            if m then
                table.insert(result, {
                    name = m.Name or "???",
                    address = toHex(m.Address or 0),
                    size = m.Size or 0,
                    is_64bit = m.Is64Bit or false,
                    path = m.PathToFile or ""
                })
            end
        end
    end
    
    -- 回退：如果找不到模块，尝试通过MZ头扫描和导出目录名称读取来查找它们
    if #result == 0 then
        local mzScan = AOBScan("4D 5A 90 00 03 00 00 00")  -- MZ PE头
        if mzScan and mzScan.Count > 0 then
            for i = 0, math.min(mzScan.Count - 1, 50) do
                local addr = tonumber(mzScan.getString(i), 16)
                if addr then
                    local peOffset = readInteger(addr + 0x3C)
                    local moduleSize = 0
                    local realName = nil
                    
                    if peOffset and peOffset > 0 and peOffset < 0x1000 then
                        -- 获取映像大小
                        local sizeOfImage = readInteger(addr + peOffset + 0x50)
                        if sizeOfImage then moduleSize = sizeOfImage end
                        
                        -- 从导出目录读取内部名称
                        local exportRVA = readInteger(addr + peOffset + 0x78)
                        if exportRVA and exportRVA > 0 and exportRVA < 0x10000000 then
                            local nameRVA = readInteger(addr + exportRVA + 0x0C)
                            if nameRVA and nameRVA > 0 and nameRVA < 0x10000000 then
                                local name = readString(addr + nameRVA, 64)
                                if name and #name > 0 and #name < 60 then
                                    realName = name
                                end
                            end
                        end
                    end
                    
                    -- 确定模块名称
                    local modName
                    if realName then
                        modName = realName
                    elseif i == 0 then
                        modName = (process ~= "" and process) or "L2.exe"
                    else
                        modName = "Module_" .. string.format("%X", addr)
                    end
                    
                    table.insert(result, {
                        name = modName,
                        address = toHex(addr),
                        size = moduleSize,
                        is_64bit = false,
                        path = "",
                        source = realName and "export_directory" or "aob_fallback"
                    })
                end
            end
            mzScan.destroy()
        end
    end
    
    return { success = true, modules = result, count = #result, fallback_used = #result > 0 and result[1] and result[1].source ~= nil }
end

local function cmd_get_symbol_address(params)
    local symbol = params.symbol or params.name
    if not symbol then return { success = false, error = "没有符号名" } end
    
    local addr = getAddressSafe(symbol)
    if addr then
        return { success = true, symbol = symbol, address = toHex(addr), value = addr }
    end
    return { success = false, error = "符号未找到: " .. symbol }
end

-- ============================================================================
-- 命令处理程序 - 内存读取
-- ============================================================================

local function cmd_read_memory(params)
    local addr = params.address
    local size = math.min(params.size or 256, 65536)  -- 限制最大读取大小
    
    if type(addr) == "string" then addr = getAddressSafe(addr) end
    if not addr then return { success = false, error = "无效地址" } end
    
    local bytes = readBytes(addr, size, true)
    if not bytes then return { success = false, error = "在 " .. toHex(addr) .. " 读取失败" } end
    
    local hex = {}
    for i, b in ipairs(bytes) do hex[i] = string.format("%02X", b) end
    
    return { 
        success = true, 
        address = toHex(addr), 
        size = #bytes, 
        data = table.concat(hex, " "),
        bytes = bytes
    }
end

local function cmd_read_integer(params)
    local addr = params.address
    local itype = params.type or "dword"
    
    if type(addr) == "string" then addr = getAddressSafe(addr) end
    if not addr then return { success = false, error = "无效地址" } end
    
    local val
    if itype == "byte" then
        local b = readBytes(addr, 1, true)
        if b and #b > 0 then val = b[1] end
    elseif itype == "word" then val = readSmallInteger(addr)
    elseif itype == "dword" then val = readInteger(addr)
    elseif itype == "qword" then val = readQword(addr)
    elseif itype == "float" then val = readFloat(addr)
    elseif itype == "double" then val = readDouble(addr)
    else return { success = false, error = "未知类型: " .. tostring(itype) } end
    
    if val == nil then return { success = false, error = "在 " .. toHex(addr) .. " 读取失败" } end
    
    return { success = true, address = toHex(addr), value = val, type = itype, hex = toHex(val) }
end

local function cmd_read_string(params)
    local addr = params.address
    local maxlen = params.max_length or 256
    local wide = params.wide or false
    
    if type(addr) == "string" then addr = getAddressSafe(addr) end
    if not addr then return { success = false, error = "无效地址" } end
    
    local str = readString(addr, maxlen, wide)
    
    -- 为JSON兼容性清理不可打印字符
    local sanitized = ""
    if str then
        for i = 1, #str do
            local byte = str:byte(i)
            if byte >= 32 and byte < 127 then
                sanitized = sanitized .. str:sub(i, i)
            elseif byte == 9 or byte == 10 or byte == 13 then
                sanitized = sanitized .. " "  -- 用空格替换制表符/换行符
            else
                sanitized = sanitized .. string.format("\\x%02X", byte)
            end
        end
    end
    
    return { success = true, address = toHex(addr), value = sanitized, wide = wide, length = str and #str or 0, raw_length = #sanitized }
end

local function cmd_read_pointer(params)
    local base = params.base or params.address
    local offsets = params.offsets or {}
    
    if type(base) == "string" then base = getAddressSafe(base) end
    if not base then return { success = false, error = "无效基地址" } end
    
    local currentAddr = base
    local path = { toHex(base) }
    
    for i, offset in ipairs(offsets) do
        -- 使用readPointer进行32/64位兼容（32位上readInteger，64位上readQword）
        local ptr = readPointer(currentAddr)
        if not ptr then
            return { success = false, error = "在 " .. toHex(currentAddr) .. " 读取指针失败", path = path }
        end
        currentAddr = ptr + offset
        table.insert(path, toHex(currentAddr))
    end
    
    -- 使用readPointer进行32/64位兼容读取最终值
    local finalValue = readPointer(currentAddr)
    return { 
        success = true, 
        base = toHex(base), 
        final_address = toHex(currentAddr), 
        value = finalValue, 
        path = path 
    }
end

-- ============================================================================
-- 命令处理程序 - 模式扫描
-- ============================================================================

local function cmd_aob_scan(params)
    local pattern = params.pattern
    local protection = params.protection or "+X"
    local limit = params.limit or 100
    
    if not pattern then return { success = false, error = "没有提供模式" } end
    
    local results = AOBScan(pattern, protection)
    if not results then return { success = true, count = 0, addresses = {} } end
    
    local addresses = {}
    for i = 0, math.min(results.Count - 1, limit - 1) do
        local addrStr = results.getString(i)
        local addr = tonumber(addrStr, 16)
        table.insert(addresses, { 
            address = "0x" .. addrStr, 
            value = addr 
        })
    end
    results.destroy()
    
    return { success = true, count = #addresses, pattern = pattern, addresses = addresses }
end

local function cmd_scan_all(params)
    local value = params.value
    local vtype = params.type or "dword"
    
    local ms = createMemScan()
    local scanOpt = soExactValue
    local varType = vtDword
    
    if vtype == "byte" then varType = vtByte
    elseif vtype == "word" then varType = vtWord
    elseif vtype == "qword" then varType = vtQword
    elseif vtype == "float" then varType = vtSingle
    elseif vtype == "double" then varType = vtDouble
    elseif vtype == "string" then varType = vtString end
    
    -- 如果提供了特定保护标志则使用（默认为Python中的+W-C）
    -- 关键：限制扫描到用户模式空间(0x7FFFFFFFFFFFFFFF)以防止内核/保护区域中的蓝屏
    local protect = params.protection or "+W-C"
    ms.firstScan(scanOpt, varType, rtRounded, tostring(value), nil, 0, 0x7FFFFFFFFFFFFFFF, protect, fsmNotAligned, "1", false, false, false, false)
    ms.waitTillDone()
    
    local fl = createFoundList(ms)
    fl.initialize()
    local count = fl.getCount()
    
    serverState.scan_memscan = ms
    serverState.scan_foundlist = fl
    
    return { success = true, count = count }
end

local function cmd_get_scan_results(params)
    local max = params.max or 100
    
    if not serverState.scan_foundlist then 
        return { success = false, error = "没有扫描结果。请先运行scan_all。" } 
    end
    
    local fl = serverState.scan_foundlist
    local results = {}
    local count = math.min(fl.getCount(), max)
    
    for i = 0, count - 1 do
        -- 重要：确保地址有0x前缀以与其他所有命令保持一致
        local addrStr = fl.getAddress(i)
        if addrStr and not addrStr:match("^0x") and not addrStr:match("^0X") then
            addrStr = "0x" .. addrStr
        end
        table.insert(results, { 
            address = addrStr, 
            value = fl.getValue(i) 
        })
    end
    
    return { success = true, results = results, total = fl.getCount(), returned = count }
end

-- ============================================================================
-- 命令处理程序 - 反汇编和分析
-- ============================================================================

local function cmd_disassemble(params)
    local addr = params.address
    local count = params.count or 20
    
    if type(addr) == "string" then addr = getAddressSafe(addr) end
    if not addr then return { success = false, error = "无效地址" } end
    
    local instructions = {}
    local currentAddr = addr
    
    for i = 1, count do
        local ok, disasm = pcall(disassemble, currentAddr)
        if not ok or not disasm then break end
        
        local instSize = getInstructionSize(currentAddr) or 1
        local instBytes = readBytes(currentAddr, instSize, true) or {}
        local bytesHex = {}
        for _, b in ipairs(instBytes) do table.insert(bytesHex, string.format("%02X", b)) end
        
        table.insert(instructions, {
            address = toHex(currentAddr),
            offset = currentAddr - addr,
            size = instSize,
            bytes = table.concat(bytesHex, " "),
            instruction = disasm
        })
        
        currentAddr = currentAddr + instSize
    end
    
    return { success = true, start_address = toHex(addr), count = #instructions, instructions = instructions }
end

local function cmd_get_instruction_info(params)
    local addr = params.address
    
    if type(addr) == "string" then addr = getAddressSafe(addr) end
    if not addr then return { success = false, error = "无效地址" } end
    
    local ok, disasm = pcall(disassemble, addr)
    if not ok or not disasm then
        return { success = false, error = "在 " .. toHex(addr) .. " 反汇编失败" }
    end
    local size = getInstructionSize(addr)
    local bytes = readBytes(addr, size or 1, true) or {}
    local bytesHex = {}
    for _, b in ipairs(bytes) do table.insert(bytesHex, string.format("%02X", b)) end
    
    local prevAddr = getPreviousOpcode(addr)
    
    return {
        success = true,
        address = toHex(addr),
        instruction = disasm,
        size = size,
        bytes = table.concat(bytesHex, " "),
        previous_instruction = prevAddr and toHex(prevAddr) or nil
    }
end

local function cmd_find_function_boundaries(params)
    local addr = params.address
    local maxSearch = params.max_search or 4096
    
    if type(addr) == "string" then addr = getAddressSafe(addr) end
    if not addr then return { success = false, error = "无效地址" } end
    
    local is64 = targetIs64Bit()
    
    -- 向后搜索函数前言
    -- 32位: push ebp; mov ebp, esp (55 8B EC)
    -- 64位: push rbp; mov rbp, rsp (55 48 89 E5) 或 sub rsp, X 模式
    local funcStart = nil
    local prologueType = nil
    for offset = 0, maxSearch do
        local checkAddr = addr - offset
        local b1 = readBytes(checkAddr, 1, false)
        local b2 = readBytes(checkAddr + 1, 1, false)
        local b3 = readBytes(checkAddr + 2, 1, false)
        local b4 = readBytes(checkAddr + 3, 1, false)
        
        -- 32位前言: push ebp; mov ebp, esp (55 8B EC)
        if b1 == 0x55 and b2 == 0x8B and b3 == 0xEC then
            funcStart = checkAddr
            prologueType = "x86_standard"
            break
        end
        
        -- 64位前言: push rbp; mov rbp, rsp (55 48 89 E5)
        if is64 and b1 == 0x55 and b2 == 0x48 and b3 == 0x89 and b4 == 0xE5 then
            funcStart = checkAddr
            prologueType = "x64_standard"
            break
        end
        
        -- 64位替代: sub rsp, imm8 (48 83 EC xx) - 在叶子函数中常见
        if is64 and b1 == 0x48 and b2 == 0x83 and b3 == 0xEC then
            funcStart = checkAddr
            prologueType = "x64_leaf"
            break
        end
    end
    
    -- 向前搜索返回指令
    local funcEnd = nil
    if funcStart then
        for offset = 0, maxSearch do
            local b = readBytes(funcStart + offset, 1, false)
            if b == 0xC3 or b == 0xC2 then
                funcEnd = funcStart + offset
                break
            end
        end
    end
    
    if funcStart then
        return {
            success = true,
            start = toHex(funcStart),
            start_offset = funcStart - addr,
            end_addr = funcEnd and toHex(funcEnd) or nil,
            end_offset = funcEnd and (funcEnd - addr) or nil,
            prologue_type = prologueType
        }
    else
        return { success = false, error = "在 " .. maxSearch .. " 字节内未找到函数前言" }
    end
end

local function cmd_analyze_function(params)
    local addr = params.address
    
    if type(addr) == "string" then addr = getAddressSafe(addr) end
    if not addr then return { success = false, error = "无效地址" } end
    
    local is64 = targetIs64Bit()
    
    -- 使用架构感知的前言检测查找函数开始
    local funcStart = nil
    local prologueType = nil
    for offset = 0, 4096 do
        local checkAddr = addr - offset
        local b1 = readBytes(checkAddr, 1, false)
        local b2 = readBytes(checkAddr + 1, 1, false)
        local b3 = readBytes(checkAddr + 2, 1, false)
        local b4 = readBytes(checkAddr + 3, 1, false)
        
        -- 32位前言: push ebp; mov ebp, esp (55 8B EC)
        if b1 == 0x55 and b2 == 0x8B and b3 == 0xEC then
            funcStart = checkAddr
            prologueType = "x86_standard"
            break
        end
        
        -- 64位前言: push rbp; mov rbp, rsp (55 48 89 E5)
        if is64 and b1 == 0x55 and b2 == 0x48 and b3 == 0x89 and b4 == 0xE5 then
            funcStart = checkAddr
            prologueType = "x64_standard"
            break
        end
        
        -- 64位替代: sub rsp, imm8 (48 83 EC xx)
        if is64 and b1 == 0x48 and b2 == 0x83 and b3 == 0xEC then
            funcStart = checkAddr
            prologueType = "x64_leaf"
            break
        end
    end
    
    if not funcStart then 
        return { 
            success = false, 
            error = "找不到函数开始",
            arch = is64 and "x64" or "x86",
            query_address = toHex(addr)
        } 
    end
    
    -- 分析函数内的调用
    local calls = {}
    local funcEnd = nil
    local currentAddr = funcStart
    
    while currentAddr < funcStart + 0x2000 do
        local instSize = getInstructionSize(currentAddr)
        if not instSize or instSize == 0 then break end
        
        local b1 = readBytes(currentAddr, 1, false)
        if b1 == 0xC3 or b1 == 0xC2 then
            funcEnd = currentAddr
            break
        end
        
        -- 检测CALL指令
        -- E8 xx xx xx xx = 相对CALL（最常见）
        if b1 == 0xE8 then
            local relOffset = readInteger(currentAddr + 1)
            if relOffset then
                if relOffset > 0x7FFFFFFF then relOffset = relOffset - 0x100000000 end
                table.insert(calls, {
                    call_site = toHex(currentAddr),
                    target = toHex(currentAddr + 5 + relOffset),
                    type = "relative"
                })
            end
        end
        
        -- FF /2 = 间接CALL (CALL r/m32 或 CALL r/m64)
        if b1 == 0xFF then
            local b2 = readBytes(currentAddr + 1, 1, false)
            if b2 and (b2 >= 0x10 and b2 <= 0x1F) then  -- ModR/M for /2
                local disasm = disassemble(currentAddr)
                table.insert(calls, {
                    call_site = toHex(currentAddr),
                    instruction = disasm,
                    type = "indirect"
                })
            end
        end
        
        currentAddr = currentAddr + instSize
    end
    
    return {
        success = true,
        function_start = toHex(funcStart),
        function_end = funcEnd and toHex(funcEnd) or nil,
        prologue_type = prologueType,
        arch = is64 and "x64" or "x86",
        call_count = #calls,
        calls = calls
    }
end

-- ============================================================================
-- 命令处理程序 - 引用查找
-- ============================================================================

local function cmd_find_references(params)
    local targetAddr = params.address
    local limit = params.limit or 50
    
    if type(targetAddr) == "string" then targetAddr = getAddressSafe(targetAddr) end
    if not targetAddr then return { success = false, error = "无效地址" } end
    
    local is64 = targetIs64Bit()
    local pattern
    
    -- 将地址转换为AOB模式（小端序）
    if is64 and targetAddr > 0xFFFFFFFF then
        -- 64位地址：8字节小端序
        local bytes = {}
        local tempAddr = targetAddr
        for i = 1, 8 do
            bytes[i] = tempAddr % 256
            tempAddr = math.floor(tempAddr / 256)
        end
        pattern = string.format("%02X %02X %02X %02X %02X %02X %02X %02X", 
            bytes[1], bytes[2], bytes[3], bytes[4], bytes[5], bytes[6], bytes[7], bytes[8])
    else
        -- 32位地址：4字节小端序
        local b1 = targetAddr % 256
        local b2 = math.floor(targetAddr / 256) % 256
        local b3 = math.floor(targetAddr / 65536) % 256
        local b4 = math.floor(targetAddr / 16777216) % 256
        pattern = string.format("%02X %02X %02X %02X", b1, b2, b3, b4)
    end
    
    local results = AOBScan(pattern, "+X")
    if not results then return { success = true, target = toHex(targetAddr), count = 0, references = {}, arch = is64 and "x64" or "x86" } end
    
    local refs = {}
    for i = 0, math.min(results.Count - 1, limit - 1) do
        local refAddr = tonumber(results.getString(i), 16)
        local disasm = disassemble(refAddr) or "???"
        table.insert(refs, {
            address = toHex(refAddr),
            instruction = disasm
        })
    end
    results.destroy()
    
    return { success = true, target = toHex(targetAddr), count = #refs, references = refs, arch = is64 and "x64" or "x86" }
end

local function cmd_find_call_references(params)
    local funcAddr = params.address or params.function_address
    local limit = params.limit or 100
    
    if type(funcAddr) == "string" then funcAddr = getAddressSafe(funcAddr) end
    if not funcAddr then return { success = false, error = "无效函数地址" } end
    
    local callers = {}
    local results = AOBScan("E8 ?? ?? ?? ??", "+X")
    
    if results then
        for i = 0, results.Count - 1 do
            if #callers >= limit then break end
            
            local callAddr = tonumber(results.getString(i), 16)
            local relOffset = readInteger(callAddr + 1)
            
            if relOffset then
                if relOffset > 0x7FFFFFFF then relOffset = relOffset - 0x100000000 end
                local target = callAddr + 5 + relOffset
                
                if target == funcAddr then
                    table.insert(callers, {
                        caller_address = toHex(callAddr),
                        instruction = disassemble(callAddr) or "???"
                    })
                end
            end
        end
        results.destroy()
    end
    
    return { success = true, function_address = toHex(funcAddr), count = #callers, callers = callers }
end

-- ============================================================================
-- 命令处理程序 - 断点
-- ============================================================================

local function cmd_set_breakpoint(params)
    local addr = params.address
    local bpId = params.id
    local captureRegs = params.capture_registers ~= false
    local captureStackFlag = params.capture_stack or false
    local stackDepth = params.stack_depth or 16
    
    if type(addr) == "string" then addr = getAddressSafe(addr) end
    if not addr then return { success = false, error = "无效地址" } end
    
    bpId = bpId or tostring(addr)
    
    -- 查找空闲的硬件槽（最多4个调试寄存器）
    local slot = nil
    for i = 1, 4 do
        if not serverState.hw_bp_slots[i] then
            slot = i
            break
        end
    end
    
    if not slot then
        return { success = false, error = "没有空闲的硬件断点槽（最多4个调试寄存器）" }
    end
    
    -- 移除此地址的现有断点
    pcall(function() debug_removeBreakpoint(addr) end)
    
    serverState.breakpoint_hits[bpId] = {}
    
    -- 关键：使用bpmDebugRegister用于硬件断点（反作弊安全）
    -- 签名：debug_setBreakpoint(address, size, trigger, breakpointmethod, function)
    debug_setBreakpoint(addr, 1, bptExecute, bpmDebugRegister, function()
        local hitData = {
            id = bpId,
            address = toHex(addr),
            timestamp = os.time(),
            breakpoint_type = "hardware_execute"
        }
        
        if captureRegs then
            hitData.registers = captureRegisters()
        end
        
        if captureStackFlag then
            hitData.stack = captureStack(stackDepth)
        end
        
        table.insert(serverState.breakpoint_hits[bpId], hitData)
        debug_continueFromBreakpoint(co_run)
        return 1
    end)
    
    serverState.hw_bp_slots[slot] = { id = bpId, address = addr }
    serverState.breakpoints[bpId] = { address = addr, slot = slot, type = "execute" }
    return { success = true, id = bpId, address = toHex(addr), slot = slot, method = "hardware_debug_register" }
end

local function cmd_set_data_breakpoint(params)
    local addr = params.address
    local bpId = params.id
    local accessType = params.access_type or "w"  -- r, w, rw
    local size = params.size or 4
    
    if type(addr) == "string" then addr = getAddressSafe(addr) end
    if not addr then return { success = false, error = "无效地址" } end
    
    bpId = bpId or tostring(addr)
    
    -- 查找空闲的硬件槽（最多4个调试寄存器）
    local slot = nil
    for i = 1, 4 do
        if not serverState.hw_bp_slots[i] then
            slot = i
            break
        end
    end
    
    if not slot then
        return { success = false, error = "没有空闲的硬件断点槽（最多4个调试寄存器）" }
    end
    
    local bpType = bptWrite
    if accessType == "r" then bpType = bptAccess
    elseif accessType == "rw" then bpType = bptAccess end
    
    serverState.breakpoint_hits[bpId] = {}
    
    -- 关键：使用bpmDebugRegister用于硬件断点（反作弊安全）
    -- 签名：debug_setBreakpoint(address, size, trigger, breakpointmethod, function)
    debug_setBreakpoint(addr, size, bpType, bpmDebugRegister, function()
        local arch = getArchInfo()
        local instPtr = arch.instPtr
        local hitData = {
            id = bpId,
            type = "data_" .. accessType,
            address = toHex(addr),
            timestamp = os.time(),
            breakpoint_type = "hardware_data",
            value = arch.is64bit and readQword(addr) or readInteger(addr),
            registers = captureRegisters(),
            instruction = instPtr and disassemble(instPtr) or "???",
            arch = arch.is64bit and "x64" or "x86"
        }
        
        table.insert(serverState.breakpoint_hits[bpId], hitData)
        debug_continueFromBreakpoint(co_run)
        return 1
    end)
    
    serverState.hw_bp_slots[slot] = { id = bpId, address = addr }
    serverState.breakpoints[bpId] = { address = addr, slot = slot, type = "data" }
    
    return { success = true, id = bpId, address = toHex(addr), slot = slot, access_type = accessType, method = "hardware_debug_register" }
end

local function cmd_remove_breakpoint(params)
    local bpId = params.id
    
    if bpId and serverState.breakpoints[bpId] then
        local bp = serverState.breakpoints[bpId]
        pcall(function() debug_removeBreakpoint(bp.address) end)
        
        if bp.slot then
            serverState.hw_bp_slots[bp.slot] = nil
        end
        
        serverState.breakpoints[bpId] = nil
        return { success = true, id = bpId }
    end
    
    return { success = false, error = "找不到断点: " .. tostring(bpId) }
end

local function cmd_get_breakpoint_hits(params)
    local bpId = params.id
    local clear = params.clear ~= false
    
    local hits
    if bpId then
        hits = serverState.breakpoint_hits[bpId] or {}
        if clear then serverState.breakpoint_hits[bpId] = {} end
    else
        -- 获取所有命中
        hits = {}
        for id, hitsForBp in pairs(serverState.breakpoint_hits) do
            for _, hit in ipairs(hitsForBp) do
                table.insert(hits, hit)
            end
        end
        if clear then serverState.breakpoint_hits = {} end
    end
    
    return { success = true, count = #hits, hits = hits }
end

local function cmd_list_breakpoints(params)
    local list = {}
    for id, bp in pairs(serverState.breakpoints) do
        table.insert(list, {
            id = id,
            address = toHex(bp.address),
            type = bp.type or "execution",
            slot = bp.slot
        })
    end
    return { success = true, count = #list, breakpoints = list }
end

local function cmd_clear_all_breakpoints(params)
    local count = 0
    for id, bp in pairs(serverState.breakpoints) do
        pcall(function() debug_removeBreakpoint(bp.address) end)
        count = count + 1
    end
    serverState.breakpoints = {}
    serverState.breakpoint_hits = {}
    serverState.hw_bp_slots = {}
    return { success = true, removed = count }
end

-- ============================================================================
-- 命令处理程序 - Lua求值
-- ============================================================================

local function cmd_evaluate_lua(params)
    local code = params.code
    if not code then return { success = false, error = "没有提供代码" } end
    
    local fn, err = loadstring(code)
    if not fn then return { success = false, error = "编译错误: " .. tostring(err) } end
    
    local ok, result = pcall(fn)
    if not ok then return { success = false, error = "运行时错误: " .. tostring(result) } end
    
    return { success = true, result = tostring(result) }
end

-- ============================================================================
-- 命令处理程序 - 内存区域
-- ============================================================================

local function cmd_get_memory_regions(params)
    local regions = {}
    local maxRegions = params.max or 100
    local pageSize = 0x1000  -- 4KB页
    
    -- 在常见基址处采样内存以查找有效区域
    local sampleAddresses = {
        0x00010000, 0x00400000, 0x10000000, 0x20000000, 0x30000000,
        0x40000000, 0x50000000, 0x60000000, 0x70000000
    }
    
    -- 还添加通过AOB扫描找到的模块地址
    local mzScan = AOBScan("4D 5A 90 00 03 00")
    if mzScan and mzScan.Count > 0 then
        for i = 0, math.min(mzScan.Count - 1, 20) do
            local addr = tonumber(mzScan.getString(i), 16)
            if addr then table.insert(sampleAddresses, addr) end
        end
        mzScan.destroy()
    end
    
    -- 检查每个采样地址的内存保护
    for _, baseAddr in ipairs(sampleAddresses) do
        if #regions >= maxRegions then break end
        
        local ok, prot = pcall(getMemoryProtection, baseAddr)
        if ok and prot then
            -- 找到有效的内存页
            local protStr = ""
            if prot.r then protStr = protStr .. "R" end
            if prot.w then protStr = protStr .. "W" end
            if prot.x then protStr = protStr .. "X" end
            
            -- 尝试通过向前扫描查找区域大小
            local regionSize = pageSize
            for offset = pageSize, 0x1000000, pageSize do
                local ok2, prot2 = pcall(getMemoryProtection, baseAddr + offset)
                if not ok2 or not prot2 or 
                   prot2.r ~= prot.r or prot2.w ~= prot.w or prot2.x ~= prot.x then
                    break
                end
                regionSize = offset + pageSize
            end
            
            table.insert(regions, {
                base = toHex(baseAddr),
                size = regionSize,
                protection = protStr,
                readable = prot.r or false,
                writable = prot.w or false,
                executable = prot.x or false
            })
        end
    end
    
    return { success = true, count = #regions, regions = regions }
end

-- ============================================================================
-- 命令处理程序 - 实用工具
-- ============================================================================

local function cmd_ping(params)
    return {
        success = true,
        version = VERSION,
        timestamp = os.time(),
        process_id = getOpenedProcessID() or 0,
        message = "CE MCP Bridge v" .. VERSION .. " 运行中"
    }
end

local function cmd_search_string(params)
    local searchStr = params.string or params.pattern
    local wide = params.wide or false
    local limit = params.limit or 100
    
    if not searchStr then return { success = false, error = "没有搜索字符串" } end
    
    -- 将字符串转换为AOB模式
    local pattern = ""
    for i = 1, #searchStr do
        if i > 1 then pattern = pattern .. " " end
        pattern = pattern .. string.format("%02X", searchStr:byte(i))
        if wide then pattern = pattern .. " 00" end
    end
    
    local results = AOBScan(pattern)
    if not results then return { success = true, count = 0, addresses = {} } end
    
    local addresses = {}
    for i = 0, math.min(results.Count - 1, limit - 1) do
        local addr = tonumber(results.getString(i), 16)
        local preview = readString(addr, 50, wide) or ""
        table.insert(addresses, {
            address = "0x" .. results.getString(i),
            preview = preview
        })
    end
    results.destroy()
    
    return { success = true, count = #addresses, addresses = addresses }
end

-- ============================================================================
-- 命令处理程序 - 高级分析工具
-- ============================================================================

-- 解析结构：使用CE的Structure.autoGuess将内存映射到类型化字段
local function cmd_dissect_structure(params)
    local address = params.address
    local size = params.size or 256
    
    if type(address) == "string" then address = getAddressSafe(address) end
    if not address then return { success = false, error = "无效地址" } end
    
    -- 创建临时结构并使用autoGuess
    local ok, struct = pcall(createStructure, "MCP_TempStruct")
    if not ok or not struct then
        return { success = false, error = "创建结构失败" }
    end
    
    -- 使用Structure类的autoGuess方法
    pcall(function() struct:autoGuess(address, 0, size) end)
    
    local elements = {}
    local count = struct.Count or 0
    
    for i = 0, count - 1 do
        local elem = struct.Element[i]
        if elem then
            local val = nil
            -- 尝试获取当前值
            pcall(function() val = elem:getValue(address) end)
            
            table.insert(elements, {
                offset = elem.Offset,
                hex_offset = string.format("+0x%X", elem.Offset),
                name = elem.Name or "",
                vartype = elem.Vartype,
                bytesize = elem.Bytesize,
                current_value = val
            })
        end
    end
    
    -- 清理 - 不添加到全局列表
    pcall(function() struct:removeFromGlobalStructureList() end)
    
    return {
        success = true,
        base_address = toHex(address),
        size_analyzed = size,
        element_count = #elements,
        elements = elements
    }
end

-- 获取线程列表：返回附加进程中所有线程
local function cmd_get_thread_list(params)
    local list = createStringlist()
    getThreadlist(list)
    
    local threads = {}
    for i = 0, list.Count - 1 do
        local idHex = list[i]
        table.insert(threads, {
            id_hex = idHex,
            id_int = tonumber(idHex, 16)
        })
    end
    
    list.destroy()
    
    return {
        success = true,
        count = #threads,
        threads = threads
    }
end

-- AutoAssemble：执行AutoAssembler脚本
local function cmd_auto_assemble(params)
    local script = params.script or params.code
    local disable = params.disable or false
    
    if not script then return { success = false, error = "没有提供脚本" } end
    
    local success, disableInfo = autoAssemble(script)
    
    if success then
        local result = {
            success = true,
            executed = true
        }
        -- 如果返回disable信息，包含符号地址
        if disableInfo and disableInfo.symbols then
            result.symbols = {}
            for name, addr in pairs(disableInfo.symbols) do
                result.symbols[name] = toHex(addr)
            end
        end
        return result
    else
        return {
            success = false,
            error = "AutoAssemble失败: " .. tostring(disableInfo)
        }
    end
end

-- 枚举内存区域完整：使用CE的原生enumMemoryRegions获取准确数据
local function cmd_enum_memory_regions_full(params)
    local maxRegions = params.max or 500
    
    local ok, regions = pcall(enumMemoryRegions)
    if not ok or not regions then
        return { success = false, error = "enumMemoryRegions失败" }
    end
    
    local result = {}
    for i, r in ipairs(regions) do
        if i > maxRegions then break end
        
        -- 确定保护字符串
        local prot = r.Protect or 0
        local state = r.State or 0
        local protStr = ""
        
        -- PAGE_EXECUTE标志
        if prot == 0x10 then protStr = "X"
        elseif prot == 0x20 then protStr = "RX"
        elseif prot == 0x40 then protStr = "RWX"
        elseif prot == 0x80 then protStr = "WX"
        elseif prot == 0x02 then protStr = "R"
        elseif prot == 0x04 then protStr = "RW"
        elseif prot == 0x08 then protStr = "W"
        else protStr = string.format("0x%X", prot)
        end
        
        table.insert(result, {
            base = toHex(r.BaseAddress or 0),
            allocation_base = toHex(r.AllocationBase or 0),
            size = r.RegionSize or 0,
            state = state,
            protect = prot,
            protect_string = protStr,
            type = r.Type or 0,
            -- 状态解码
            is_committed = state == 0x1000,
            is_reserved = state == 0x2000,
            is_free = state == 0x10000
        })
    end
    
    return {
        success = true,
        count = #result,
        regions = result
    }
end

-- 读取指针链：跟随指针链以解析动态地址
local function cmd_read_pointer_chain(params)
    local base = params.base
    local offsets = params.offsets or {}
    
    if type(base) == "string" then base = getAddressSafe(base) end
    if not base then return { success = false, error = "无效基地址" } end
    
    local currentAddr = base
    local chain = { { step = 0, address = toHex(currentAddr), description = "base" } }
    
    for i, offset in ipairs(offsets) do
        -- 读取当前地址的指针
        local ptr = readPointer(currentAddr)
        if not ptr then
            return {
                success = false,
                error = "在第 " .. i .. " 步读取指针失败",
                partial_chain = chain,
                failed_at_address = toHex(currentAddr)
            }
        end
        
        -- 应用偏移
        currentAddr = ptr + offset
        table.insert(chain, {
            step = i,
            address = toHex(currentAddr),
            offset = offset,
            hex_offset = string.format("+0x%X", offset),
            pointer_value = toHex(ptr)
        })
    end
    
    -- 尝试读取最终地址的值（使用readPointer进行32/64位兼容）
    local finalValue = nil
    pcall(function()
        finalValue = readPointer(currentAddr)
    end)
    
    return {
        success = true,
        base = toHex(base),
        offsets = offsets,
        final_address = toHex(currentAddr),
        final_value = finalValue,
        chain = chain
    }
end

-- 获取RTTI类名：使用C++ RTTI识别对象类型
local function cmd_get_rtti_classname(params)
    local address = params.address
    
    if type(address) == "string" then address = getAddressSafe(address) end
    if not address then return { success = false, error = "无效地址" } end
    
    local className = getRTTIClassName(address)
    
    if className then
        return {
            success = true,
            address = toHex(address),
            class_name = className,
            found = true
        }
    else
        return {
            success = true,
            address = toHex(address),
            class_name = nil,
            found = false,
            note = "在此地址找不到RTTI信息"
        }
    end
end

-- 获取地址信息：将原始地址转换为符号名称（模块+偏移）
local function cmd_get_address_info(params)
    local address = params.address
    local includeModules = params.include_modules ~= false  -- 默认true
    local includeSymbols = params.include_symbols ~= false  -- 默认true
    local includeSections = params.include_sections or false  -- 默认false
    
    if type(address) == "string" then address = getAddressSafe(address) end
    if not address then return { success = false, error = "无效地址" } end
    
    local symbolicName = getNameFromAddress(address, includeModules, includeSymbols, includeSections)
    
    -- inModule()可能在反作弊环境中失败或返回nil，所以我们也要检查symbolicName
    local isInModule = false
    local okInMod, inModResult = pcall(inModule, address)
    if okInMod and inModResult then
        isInModule = true
    elseif symbolicName and symbolicName:match("%+") then
        -- symbolicName包含"+"如"L2.exe+1000"表示它在模块中
        isInModule = true
    end
    
    -- 确保symbolic_name有0x前缀，如果它只是十六进制地址
    if symbolicName and symbolicName:match("^%x+$") then
        symbolicName = "0x" .. symbolicName
    end
    
    return {
        success = true,
        address = toHex(address),
        symbolic_name = symbolicName or toHex(address),
        is_in_module = isInModule,
        options_used = {
            include_modules = includeModules,
            include_symbols = includeSymbols,
            include_sections = includeSections
        }
    }
end

-- 校验内存：计算内存区域的MD5哈希
local function cmd_checksum_memory(params)
    local address = params.address
    local size = params.size or 256
    
    if type(address) == "string" then address = getAddressSafe(address) end
    if not address then return { success = false, error = "无效地址" } end
    
    local ok, hash = pcall(md5memory, address, size)
    
    if ok and hash then
        return {
            success = true,
            address = toHex(address),
            size = size,
            md5_hash = hash
        }
    else
        return {
            success = false,
            address = toHex(address),
            size = size,
            error = "计算MD5失败: " .. tostring(hash)
        }
    end
end

-- 生成签名：为地址创建唯一的AOB模式（用于重新获取）
local function cmd_generate_signature(params)
    local addr = params.address
    if type(addr) == "string" then addr = getAddressSafe(addr) end
    if not addr then return { success = false, error = "无效地址" } end
    
    -- getUniqueAOB(address) 返回：AOBString, Offset
    -- 它扫描用于标识此位置的唯一字节模式
    local ok, signature, offset = pcall(getUniqueAOB, addr)
    
    if not ok then
        return {
            success = false,
            address = toHex(addr),
            error = "getUniqueAOB失败: " .. tostring(signature)
        }
    end
    
    if not signature or signature == "" then
        return {
            success = false,
            address = toHex(addr),
            error = "无法生成唯一签名 - 模式不够唯一"
        }
    end
    
    -- 计算签名长度（计数字节，通配符计为1）
    local byteCount = 0
    for _ in signature:gmatch("%S+") do
        byteCount = byteCount + 1
    end
    
    return {
        success = true,
        address = toHex(addr),
        signature = signature,
        offset_from_start = offset or 0,
        byte_count = byteCount,
        usage_hint = string.format("aob_scan('%s')然后添加偏移%d到达目标", signature, offset or 0)
    }
end

-- ============================================================================
-- DBVM虚拟机管理程序工具（安全动态跟踪 - Ring -1）
-- ============================================================================
-- 这些工具使用DBVM（可调试虚拟机）进行虚拟机管理程序级跟踪。
-- 它们对反作弊完全不可见：无游戏内存修改，无调试寄存器。
-- DBVM在虚拟机管理程序级别工作，位于OS下方，使其无法被检测到。
-- ============================================================================

-- 获取物理地址：将虚拟地址转换为物理RAM地址
-- DBVM操作需要
local function cmd_get_physical_address(params)
    local addr = params.address
    if type(addr) == "string" then addr = getAddressSafe(addr) end
    if not addr then return { success = false, error = "无效地址" } end
    
    -- 检查DBK（内核驱动程序）是否可用
    local ok, phys = pcall(dbk_getPhysicalAddress, addr)
    
    if not ok then
        return {
            success = false,
            virtual_address = toHex(addr),
            error = "DBK驱动程序未加载。首先运行dbk_initialize()或通过CE设置加载。"
        }
    end
    
    if not phys or phys == 0 then
        return {
            success = false,
            virtual_address = toHex(addr),
            error = "无法解析物理地址。页面可能不在RAM中。"
        }
    end
    
    return {
        success = true,
        virtual_address = toHex(addr),
        physical_address = toHex(phys),
        physical_int = phys
    }
end

-- 开始DBVM监视：虚拟机管理程序级内存访问监视
-- 这是"查找写入/读取内容"的等效物，但在Ring -1（对游戏不可见）
local function cmd_start_dbvm_watch(params)
    local addr = params.address
    local mode = params.mode or "w"  -- "w" = 写入, "r" = 读取, "rw" = 两者, "x" = 执行
    local maxEntries = params.max_entries or 1000  -- 内部缓冲区大小
    
    if type(addr) == "string" then addr = getAddressSafe(addr) end
    if not addr then return { success = false, error = "无效地址" } end
    
    -- 0. 安全检查
    if not dbk_initialized() then
        return { success = false, error = "DBK驱动程序未加载。转到设置->调试器->内核模式" }
    end
    
    if not dbvm_initialized() then
        -- 尝试初始化（如果可能）
        pcall(dbvm_initialize)
        if not dbvm_initialized() then
            return { success = false, error = "DBVM未运行。转到设置->调试器->使用DBVM" }
        end
    end

    -- 1. 获取物理地址（DBVM在物理RAM上工作）
    local ok, phys = pcall(dbk_getPhysicalAddress, addr)
    if not ok or not phys or phys == 0 then
        return {
            success = false,
            virtual_address = toHex(addr),
            error = "无法解析物理地址。页面可能已分页或无效。"
        }
    end
    
    -- 2. 检查是否已在监视此地址
    local watchKey = toHex(addr)
    if serverState.active_watches[watchKey] then
        return {
            success = false,
            virtual_address = toHex(addr),
            error = "已在监视此地址。首先调用stop_dbvm_watch。"
        }
    end
    
    -- 3. 配置监视选项
    -- 位0：多次记录（1 = 是）
    -- 位1：忽略大小/记录整个页面（2）
    -- 位2：记录FPU寄存器（4）
    -- 位3：记录堆栈（8）
    local options = 1 + 2 + 8  -- 多次记录+整个页面+堆栈上下文
    
    -- 4. 根据模式开始适当的监视
    local watch_id
    local okWatch, result
    
    log(string.format("在物理地址上开始DBVM监视: 0x%X (模式: %s)", phys, mode))

    if mode == "x" then
        if not dbvm_watch_executes then
            return { success = false, error = "CE Lua引擎中缺少dbvm_watch_executes函数" }
        end
        okWatch, result = pcall(dbvm_watch_executes, phys, 1, options, maxEntries)
        watch_id = okWatch and result or nil
    elseif mode == "r" or mode == "rw" then
        okWatch, result = pcall(dbvm_watch_reads, phys, 1, options, maxEntries)
        watch_id = okWatch and result or nil
    else  -- 默认：写入
        okWatch, result = pcall(dbvm_watch_writes, phys, 1, options, maxEntries)
        watch_id = okWatch and result or nil
    end
    
    if not okWatch then
        return {
            success = false,
            virtual_address = toHex(addr),
            physical_address = toHex(phys),
            error = "DBVM监视崩溃/失败: " .. tostring(result)
        }
    end
    
    if not watch_id then
        return {
            success = false,
            virtual_address = toHex(addr),
            physical_address = toHex(phys),
            error = "DBVM监视返回nil（检查CE控制台详情）"
        }
    end
    
    -- 5. 存储监视以供稍后检索
    serverState.active_watches[watchKey] = {
        id = watch_id,
        physical = phys,
        mode = mode,
        start_time = os.time()
    }
    
    return {
        success = true,
        status = "监视中",
        virtual_address = toHex(addr),
        physical_address = toHex(phys),
        watch_id = watch_id,
        mode = mode,
        note = "调用poll_dbvm_watch以获取日志而不停止，或stop_dbvm_watch以结束"
    }
end

-- 轮询DBVM监视：检索记录的访问而不停止监视
-- 这对连续数据包监视至关重要 - 日志可以重复轮询
local function cmd_poll_dbvm_watch(params)
    local addr = params.address
    local clear = params.clear or true  -- 默认清除日志后轮询
    local max_results = params.max_results or 1000
    
    if type(addr) == "string" then addr = getAddressSafe(addr) end
    if not addr then return { success = false, error = "无效地址" } end
    
    local watchKey = toHex(addr)
    local watchInfo = serverState.active_watches[watchKey]
    
    if not watchInfo then
        return {
            success = false,
            virtual_address = toHex(addr),
            error = "找不到此地址的活动监视。首先调用start_dbvm_watch。"
        }
    end
    
    local watch_id = watchInfo.id
    local results = {}
    
    -- 检索日志条目（DBVM自动累积这些）
    local okLog, log = pcall(dbvm_watch_retrievelog, watch_id)
    
    if okLog and log then
        local count = math.min(#log, max_results)
        for i = 1, count do
            local entry = log[i]
            -- 对于数据包捕获，我们需要执行时的堆栈指针来读取[ESP+4]
            -- ESP/RSP包含执行时的堆栈指针
            local hitData = {
                hit_number = i,
                -- 32位游戏使用ESP，64位使用RSP
                ESP = entry.RSP and (entry.RSP % 0x100000000) or nil,  -- 32位游戏的低32位
                RSP = entry.RSP and toHex(entry.RSP) or nil,
                EIP = entry.RIP and (entry.RIP % 0x100000000) or nil,  -- 低32位
                RIP = entry.RIP and toHex(entry.RIP) or nil,
                -- 包含可能持有数据包缓冲区的关键寄存器
                EAX = entry.RAX and (entry.RAX % 0x100000000) or nil,
                ECX = entry.RCX and (entry.RCX % 0x100000000) or nil,
                EDX = entry.RDX and (entry.RDX % 0x100000000) or nil,
                EBX = entry.RBX and (entry.RBX % 0x100000000) or nil,
                ESI = entry.RSI and (entry.RSI % 0x100000000) or nil,
                EDI = entry.RDI and (entry.RDI % 0x100000000) or nil,
            }
            table.insert(results, hitData)
        end
    end
    
    local uptime = os.time() - (watchInfo.start_time or os.time())
    
    return {
        success = true,
        status = "活动",
        virtual_address = toHex(addr),
        physical_address = toHex(watchInfo.physical),
        mode = watchInfo.mode,
        uptime_seconds = uptime,
        hit_count = #results,
        hits = results,
        note = "监视仍处于活动状态。再次调用以获取更多日志，或stop_dbvm_watch以结束。"
    }
end

-- 停止DBVM监视：检索记录的访问并禁用监视
-- 返回触摸监视内存的所有指令
local function cmd_stop_dbvm_watch(params)
    local addr = params.address
    if type(addr) == "string" then addr = getAddressSafe(addr) end
    if not addr then return { success = false, error = "无效地址" } end
    
    local watchKey = toHex(addr)
    local watchInfo = serverState.active_watches[watchKey]
    
    if not watchInfo then
        return {
            success = false,
            virtual_address = toHex(addr),
            error = "找不到此地址的活动监视"
        }
    end
    
    local watch_id = watchInfo.id
    local results = {}
    
    -- 1. 检索所有内存访问的日志
    local okLog, log = pcall(dbvm_watch_retrievelog, watch_id)
    
    if okLog and log then
        -- 解析每个日志条目（包含访问时的CPU上下文）
        for i, entry in ipairs(log) do
            local hitData = {
                hit_number = i,
                instruction_address = entry.RIP and toHex(entry.RIP) or nil,
                instruction = entry.RIP and (pcall(disassemble, entry.RIP) and disassemble(entry.RIP) or "???") or "???",
                -- 访问时的CPU寄存器
                registers = {
                    RAX = entry.RAX and toHex(entry.RAX) or nil,
                    RBX = entry.RBX and toHex(entry.RBX) or nil,
                    RCX = entry.RCX and toHex(entry.RCX) or nil,
                    RDX = entry.RDX and toHex(entry.RDX) or nil,
                    RSI = entry.RSI and toHex(entry.RSI) or nil,
                    RDI = entry.RDI and toHex(entry.RDI) or nil,
                    RBP = entry.RBP and toHex(entry.RBP) or nil,
                    RSP = entry.RSP and toHex(entry.RSP) or nil,
                    RIP = entry.RIP and toHex(entry.RIP) or nil
                }
            }
            table.insert(results, hitData)
        end
    end
    
    -- 2. 禁用监视
    pcall(dbvm_watch_disable, watch_id)
    
    -- 3. 清理
    serverState.active_watches[watchKey] = nil
    
    local duration = os.time() - (watchInfo.start_time or os.time())
    
    return {
        success = true,
        virtual_address = toHex(addr),
        physical_address = toHex(watchInfo.physical),
        mode = watchInfo.mode,
        hit_count = #results,
        duration_seconds = duration,
        hits = results,
        note = #results > 0 and "找到访问内存的指令" or "监视期间未检测到访问"
    }
end

-- ============================================================================
-- 命令调度器
-- ============================================================================

local commandHandlers = {
    -- 进程和模块
    get_process_info = cmd_get_process_info,
    enum_modules = cmd_enum_modules,
    get_symbol_address = cmd_get_symbol_address,
    
    -- 内存读取
    read_memory = cmd_read_memory,
    read_bytes = cmd_read_memory,  -- 别名
    read_integer = cmd_read_integer,
    read_string = cmd_read_string,
    read_pointer = cmd_read_pointer,
    
    -- 模式扫描
    aob_scan = cmd_aob_scan,
    pattern_scan = cmd_aob_scan,  -- 别名
    scan_all = cmd_scan_all,
    get_scan_results = cmd_get_scan_results,
    search_string = cmd_search_string,
    
    -- 反汇编和分析
    disassemble = cmd_disassemble,
    get_instruction_info = cmd_get_instruction_info,
    find_function_boundaries = cmd_find_function_boundaries,
    analyze_function = cmd_analyze_function,
    
    -- 引用查找
    find_references = cmd_find_references,
    find_call_references = cmd_find_call_references,
    
    -- 断点
    set_breakpoint = cmd_set_breakpoint,
    set_execution_breakpoint = cmd_set_breakpoint,  -- 别名
    set_data_breakpoint = cmd_set_data_breakpoint,
    set_write_breakpoint = cmd_set_data_breakpoint,  -- 别名
    remove_breakpoint = cmd_remove_breakpoint,
    get_breakpoint_hits = cmd_get_breakpoint_hits,
    list_breakpoints = cmd_list_breakpoints,
    clear_all_breakpoints = cmd_clear_all_breakpoints,
    
    -- 内存区域
    get_memory_regions = cmd_get_memory_regions,
    enum_memory_regions_full = cmd_enum_memory_regions_full,  -- 更准确，使用原生API
    
    -- Lua求值
    evaluate_lua = cmd_evaluate_lua,
    
    -- 高级分析工具
    dissect_structure = cmd_dissect_structure,
    get_thread_list = cmd_get_thread_list,
    auto_assemble = cmd_auto_assemble,
    read_pointer_chain = cmd_read_pointer_chain,
    get_rtti_classname = cmd_get_rtti_classname,
    get_address_info = cmd_get_address_info,
    checksum_memory = cmd_checksum_memory,
    generate_signature = cmd_generate_signature,
    
    -- DBVM虚拟机管理程序工具（安全动态跟踪 - Ring -1）
    get_physical_address = cmd_get_physical_address,
    start_dbvm_watch = cmd_start_dbvm_watch,
    poll_dbvm_watch = cmd_poll_dbvm_watch,  -- 轮询日志而不停止监视
    stop_dbvm_watch = cmd_stop_dbvm_watch,
    -- 语义别名为便于使用
    find_what_writes_safe = cmd_start_dbvm_watch,  -- 别名：开始监视写入
    find_what_accesses_safe = cmd_start_dbvm_watch,  -- 别名：开始监视访问
    get_watch_results = cmd_stop_dbvm_watch,  -- 别名：检索结果并停止
    
    -- 实用工具
    ping = cmd_ping,
}

-- ============================================================================
-- 主命令处理器
-- ============================================================================

local function executeCommand(jsonRequest)
    local ok, request = pcall(json.decode, jsonRequest)
    if not ok or not request then
        return json.encode({ jsonrpc = "2.0", error = { code = -32700, message = "解析错误" }, id = nil })
    end
    
    local method = request.method
    local params = request.params or {}
    local id = request.id
    
    local handler = commandHandlers[method]
    if not handler then
        return json.encode({ jsonrpc = "2.0", error = { code = -32601, message = "方法未找到: " .. tostring(method) }, id = id })
    end
    
    local ok2, result = pcall(handler, params)
    if not ok2 then
        return json.encode({ jsonrpc = "2.0", error = { code = -32603, message = "内部错误: " .. tostring(result) }, id = id })
    end
    
    return json.encode({ jsonrpc = "2.0", result = result, id = id })
end

-- ============================================================================
-- 线程式管道服务器（非阻塞GUI）
-- ============================================================================
-- 替换v10定时器架构以防止GUI冻结.
-- I/O发生在工作线程中。执行发生在主线程中。

local function PipeWorker(thread)
    log("工作线程已启动 - 等待连接...")
    
    while not thread.Terminated do
        -- 为每个连接尝试创建管道实例
        -- 增加缓冲区大小到64KB以获得更好的吞吐量
        local pipe = createPipe(PIPE_NAME, 65536, 65536)
        if not pipe then
            log("致命错误: 创建管道失败")
            return
        end
        
        -- 存储引用，以便我们可以从主线程销毁它(stopServer)以打破阻塞调用
        serverState.workerPipe = pipe
        
        -- 设置超时用于阻塞操作（连接/读取）
        -- 我们不设置pipe.Timeout，因为它会在超时时自动断开连接.
        -- 我们依赖阻塞读取和stopServer的pipe.destroy()来打破阻塞.
        -- pipe.Timeout = 0 (默认, 无限)
        
        -- 等待客户端（阻塞，但在线程中，所以GUI正常）
        -- LuaPipeServer使用acceptConnection().
        -- 注意: acceptConnection可能不会返回布尔值，所以我们检查pipe.Connected.
        
        -- log("线程: 调用acceptConnection()...")
        pcall(function()
            pipe.acceptConnection()
        end)
        
        if pipe.Connected and not thread.Terminated then
            log("客户端已连接")
            serverState.connected = true
            
            while not thread.Terminated and pipe.Connected do
                -- 尝试读取头（4字节）
                -- 我们使用pcall优雅地处理超时/错误
                local ok, lenBytes = pcall(function() return pipe.readBytes(4) end)
                
                if ok and lenBytes and #lenBytes == 4 then
                    local len = lenBytes[1] + (lenBytes[2] * 256) + (lenBytes[3] * 65536) + (lenBytes[4] * 16777216)
                    
                    -- 合理性检查长度
                    if len > 0 and len < 100 * 1024 * 1024 then
                        local payload = pipe.readString(len)
                        
                        if payload then
                            -- 关键：在主线程上执行
                            -- 我们暂停工作线程并在GUI线程上运行逻辑以确保安全
                            local response = nil
                            thread.synchronize(function()
                                response = executeCommand(payload)
                            end)
                            
                            -- 写入响应（工作线程）
                            if response then
                                local rLen = #response
                                local b1 = rLen % 256
                                local b2 = math.floor(rLen / 256) % 256
                                local b3 = math.floor(rLen / 65536) % 256
                                local b4 = math.floor(rLen / 16777216) % 256
                                
                                pipe.writeBytes({b1, b2, b3, b4})
                                pipe.writeString(response)
                            end
                        else
                             -- log("线程: 读取payload失败 (nil)")
                        end
                    end
                else
                    -- 读取失败。如果管道断开连接，循环将在下次检查时终止.
                    if not pipe.Connected then
                        -- 客户端正常断开连接
                    end
                end
            end
            
            serverState.connected = false
            log("客户端已断开连接")
        else
            -- 调试: acceptConnection返回但管道无效
            -- 这通常发生在终止或奇怪状态时
            if not thread.Terminated then
                -- log("线程: 辅助日志 - 连接尝试无效")
            end
        end
        
        -- 清理管道
        serverState.workerPipe = nil
        pcall(function() pipe.destroy() end)
        
        -- 在重新创建管道接受新连接之前短暂休眠
        if not thread.Terminated then sleep(50) end
    end
    
    log("工作线程已终止")
end

-- ============================================================================
-- 主控制
-- ============================================================================

function StopMCPBridge()
    if serverState.workerThread then
        log("正在停止服务器（终止线程）...")
        serverState.workerThread.terminate()
        
        -- 如果当前在acceptConnection或read上阻塞，则强制销毁管道
        if serverState.workerPipe then
            pcall(function() serverState.workerPipe.destroy() end)
            serverState.workerPipe = nil
        end
        
        serverState.workerThread = nil
        serverState.running = false
    end
    
    if serverState.timer then
        serverState.timer.destroy()
        serverState.timer = nil
    end
    
    -- 关键：清理所有僵尸资源（断点、DBVM监视、扫描）
    cleanupZombieState()
    
    log("服务器已停止")
end

function StartMCPBridge()
    StopMCPBridge()  -- 这现在还调用cleanupZombieState()
    
    -- 更新全局状态
    log("正在启动MCP桥接 v" .. VERSION)
    
    serverState.running = true
    serverState.connected = false
    
    -- 创建工作线程
    serverState.workerThread = createThread(PipeWorker)
    
    log("===========================================")
    log("MCP服务器监听在: " .. PIPE_NAME)
    log("架构: 线程I/O + 同步执行")
    log("清理: 僵尸预防激活")
    log("===========================================")
end

-- 自动启动
StartMCPBridge()