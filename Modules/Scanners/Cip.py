from Base.Exploits import Exploit, Option
import Base.Validators as Validators
from Utils import print_error, print_success, print_status, export_table, port_scan, printTable
from Modules.Clients.ModbusClient import Exploit as CipClient

TABLE_HEADER = ["Product Name", "Device Type", "Vendor ", "Revision", "Serial Number", "Slot", "IP Address"]
CIP_DEVICES = []


class Exploit(Exploit):
    __info__ = {
        'name': 'scanners/cip',
        'display_name': 'CIP Device Scanner',
        'authors': [
            'wenzhe zhu <jtrkid[at]gmail.com>',
            'D0ubl3G <d0ubl3g[at]protonmail.com>',
        ],
        'description': 'Scan all device which support Ethernet/IP CIP protocol.',
        'references': [
        ],
        'devices': [
            'Multi',
        ],
    }

    target = Option('', "String for hosts as nmap use it 'scanme.nmap.org'"
                                 " or '198.116.0-255.1-127' or '216.163.128.20/20'")
    port = Option(44818, 'Ethernet/IP CIP port, default is 44818/TCP', validators=Validators.integer)
    verbose = Option(0, 'Scapy verbose level, 0 to 2', validators=Validators.integer)
    max_slot = Option(5, 'Maximum PLC Slot number for scan, default is 5, set to 10 '
                                  'if you want scan up to slot 10', validators=Validators.integer)
    output_file = Option('', "output file path")
    result = []

    def get_target_info(self, host, port):
        product_name = ''
        device_type = ''
        vendor = ''
        revision = ''
        serial_number = ''
        slot = ''
        ip_address = host
        target = CipClient(name='CIP_Scanner')
        target.connect()
        for slot_num in range(self.max_slot + 1):
                print_status("Tring to scan %s with Slot%s" % (host, slot_num))
                try:
                    product_name, device_type, vendor, revision, serial_number = \
                    target.get_target_info(port_segment=slot_num)
                    print(product_name, device_type, vendor, revision, serial_number)
                    slot = slot_num
                    ip_address = host
                    if serial_number != '':
                        self.result.append([product_name, device_type, vendor, revision, serial_number,
                                            str(slot), ip_address])
                except Exception as err:
                    print_error(err)
                    return False

    def run(self):
        self.result = []
        #conf.verb = self.verbose
        nm = port_scan(protocol='TCP', target=self.target, port=self.port)
        for host in nm.all_hosts():
            if nm[host]['tcp'][self.port]['state'] == "open":
                print_success("Host: %s, port:%s is open" % (host, self.port))
                self.get_target_info(host=host, port=self.port)
        unique_device = [list(x) for x in set(tuple(x) for x in self.result)]
        unique_device = sorted(unique_device, key=lambda x: (x[5], x[6]))

        if len(self.result) > 0:
            print_success("Find %s targets" % len(self.result))
            printTable(TABLE_HEADER, *unique_device, **{'max_column_length': 20})
            print('\r')
        else:
            print_error("Didn't find any target on network %s" % self.target)

    def command_export(self, file_path, *args, **kwargs):
        unique_device = [list(x) for x in set(tuple(x) for x in self.result)]
        unique_device = sorted(unique_device, key=lambda x: (x[5], x[6]))
        export_table(file_path, TABLE_HEADER, unique_device)
