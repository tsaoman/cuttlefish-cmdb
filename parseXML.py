import defusedxml.ElementTree as ET

#takes in a filename (str) and returns a list of dictionaries (each asset and its properties)
def parseXML(file):

    #set up tree
    tree = ET.parse(file)
    root = tree.getroot()

    # assets
    assets = []

    for host in root.findall('host'):

        asset = {} #blank dict for asset attributes

        for address in host.findall('address'):

            if address.get('addrtype') == 'ipv4':
                asset['ipv4'] = address.get('addr')

            if address.get('addrtype') == 'mac':
                asset['mac'] = address.get('addr')

        assets.append(asset) #add asset to asset list

    return assets

print(parseXML('scan1.xml'))
