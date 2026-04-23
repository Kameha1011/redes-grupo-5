local protocol = Proto('ProtocoloGrupo5', 'TP Redes Grupo 5')

--[[
Header  12 Bytes

    -- mainField (32 bits)
    3 bits de tipo de paquete 
    1 bit tipo de operación 
    28 bits de tamaño del payload (primer bit se usa para indicar StopAndWait (0) o SelectiveRepeat (1))

    -- identityField (32 bits)
    32 bits de identificador
    
    -- checksumField (32 bits)
    32 bits de checksum 

-- dataField
DATA (hasta 1024 bytes)


Tipo paquete:
000  SYN
001  SYN-ACK
010  ACK
011  DATA
100  CLOSE
101  ERROR

Tipo operación:
0 Download 
1 Upload 
]]

local mainField = ProtoField.uint32('mainField', 'Principal', base.HEX)

local packetTypeSubfield = ProtoField.uint32('packetTypeSubfield', 'Tipo de Paquete', base.DEC, {
    [0]='SYN', [1]='SYN-ACK', [2]='ACK', [3]='DATA', [4]='CLOSE', [5]='ERROR'
}, 0xE0000000)

local operationTypeSubfield = ProtoField.uint32('operationTypeSubfield', 'Tipo de Operacion', base.DEC, {
    [0]='Download', [1]='Upload'
}, 0x10000000)

local protocolSubfield = ProtoField.uint32('protocolSubfield', 'Protocolo', base.DEC, {
    [0]='StopAndWait', [1]='SelectiveRepeat'
}, 0x08000000)

local payloadSizeSubfield = ProtoField.uint32('payloadSizeSubfield', 'Tamanio del Payload', base.DEC, nil, 0x07FFFFFF)


local identityField = ProtoField.uint32('identityField', 'Identificador', base.DEC)

local checksumField = ProtoField.uint32('checksumField', 'Checksum', base.HEX)


local dataField = ProtoField.bytes('dataField', 'DATA')


protocol.fields = {mainField, packetTypeSubfield, operationTypeSubfield, protocolSubfield, payloadSizeSubfield, identityField, checksumField, dataField}


-- Funcion para leer el header del paquete - hook dissector de lua
function protocol.dissector(buffer, pinfo, tree)

    pinfo.cols.protocol = 'ProtocoloGrupo5'

    local subtree = tree:add(protocol, buffer(), 'ProtocoloGrupo5')

    local mainTree = subtree:add(mainField, buffer(0,4))
    mainTree:add(packetTypeSubfield, buffer(0,4))
    mainTree:add(operationTypeSubfield, buffer(0,4))
    mainTree:add(protocolSubfield, buffer(0,4))
    mainTree:add(payloadSizeSubfield, buffer(0,4))

    subtree:add(identityField, buffer(4,4))

    subtree:add(checksumField, buffer(8,4))

    if (buffer:len() > 12) then
        subtree:add(dataField, buffer(12))
    end

end

-- Registrar el protocolo en un puerto UDP
local portUPD = 9000
local tableUDP = DissectorTable.get('udp.port')
tableUDP:add(portUPD, protocol)

