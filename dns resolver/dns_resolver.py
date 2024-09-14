import socket
import struct

class DnsHeader:
    def __init__(self, id, flags, qdcount, ancount, nscount, arcount):
        self.id = id
        self.flags = flags
        self.qdcount = qdcount
        self.ancount = ancount
        self.nscount = nscount
        self.arcount = arcount

    
    def to_bytes(self):
        return (self.id.to_bytes(2, 'big') + self.flags.to_bytes(2, 'big') + self.qdcount.to_bytes(2, 'big') +
                self.ancount.to_bytes(2, 'big') + self.nscount.to_bytes(2, 'big') + self.arcount.to_bytes(2, 'big'))
    
class DnsQuestion:
    def __init__(self, name, qtype, qclass):
        #hosname encoding
        #labels = name.split('.')
        #length_of_label = [len(label) for label in labels]
        #lenggth_label = [f"{length_of_label}{labels}" for url_lenghth, url_chunk in zip(length_of_label, labels)]
        #name = ''.join(lenggth_label)
        self.name =name #encoded url name
        self.qtype = qtype
        self.qclass = qclass

    def to_bytes(self):
        return self.name + self.qtype.to_bytes(2, 'big') + self.qclass.to_bytes(2, 'big')
class DNSMessage:
    def __init__(self, header, question):
        self.header = header
        self.question = question

    def to_bytes(self):
        return self.header.to_bytes() + self.question.to_bytes()
# Define the DNS Header
header = DnsHeader(
    id=22,  # Random ID
    flags=0x0100,  # Recursion desired bit set
    qdcount=1,  # Number of questions
    ancount=0,  # No answers
    nscount=0,  # No authority records
    arcount=0  # No additional records
)
def encode_domain(name):
    """Encodes a domain name into the DNS format"""
    parts = name.split('.')
    encoded = b''
    for part in parts:
        encoded += bytes([len(part)]) + part.encode()
    encoded += b'\x00'  # End of domain name
    return encoded
question = DnsQuestion(
    name=encode_domain('dns.google.com'),
    qtype=1,  # A record
    qclass=1  # IN class
)
server = ('8.8.8.8', 53)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
message = DNSMessage(header, question)

# Convert to bytes and print the message
message_bytes = message.to_bytes()
sock.sendto(message_bytes, server)

response, _ = sock.recvfrom(4096)
print(response)

def parse_header_section(response):
    if len(response) < 12:
        raise ValueError(f"DNS response must be at least 12 bytes long, got {len(response)} bytes")
    header_data = response[:12]

    (id, flags, qdcount, ancount, nscount, arcount) = struct.unpack("!HHHHHH", header_data)
    qr = (flags >> 15) & 1
    opcode = (flags >> 11) & 0xF
    aa = (flags >> 10) & 1
    tc = (flags >> 9)  & 1
    rd = (flags >> 8) & 1
    ra = (flags >> 7) & 1
    z = (flags >> 4) & 7
    rcode = flags & 0xF
    
    header = {}
    header["ID"], header['FLAGS'], header['QdCount'], header['AnCount'], header['NsCount']
    return header
def parse_answer_section(response, offset, an_count):
    answers = []
    for _ in range(an_count):
        name_pointer = struct.unpack("!H", response[offset:offset + 2][0])
        offset +=2 

        rtype, rclass, ttl, rdlength = struct.unpack("!2H2I", response[offset:offset + rdlength])
        offset += 10

        #Extract RDATA based on RDLENGTH
        if rtype == 1: # A record (ipv4 address)
            ip_address = struct.unpack("!4B", response[offset:offset + rdlength])
            ip_address = "".join(map(str, ip_address))
            answers.append(ip_address)
        offset += rdlength
    return answers
header = parse_header_section(response)
offset = 12
answers = parse_answer_section(response, offset, header["Ancount"])

print(answers)
