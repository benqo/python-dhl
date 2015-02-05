from suds.client import Client
from suds.wsse import Security, UsernameToken

from dhl.resources.address import DHLPerson, DHLCompany
from dhl.resources.package import DHLPackage
from dhl.resources.shipment import DHLShipment
from dhl.resources.response import DHLResponse


class DHLService:
    """
    Main class with static data and the main shipping methods.
    """
    test_url = 'https://wsb.dhl.com/sndpt/expressRateBook?wsdl'
    url = 'https://wsb.dhl.com:443/gbl/expressRateBook?wsdl'

    def __init__(self, username, password, account_number, test_mode=False):
        self.username = username
        self.password = password
        self.account_number = account_number
        self.test_mode = test_mode
        self.client = None

    def send(self, shipment, message=None):
        """
        Creates the client, the DHL shipment and makes the DHL web request.
        :param shipment: DHLShipment object
        :param message: optional message
        :return: True if successful, else False
        """
        if shipment.response and shipment.response.success:
            print('This shipment has already been sent. Please create a new shipment.')
            return False

        if not self.client:
            url = self.test_url if self.test_mode else self.url
            self.client = Client(url, faults=False)

            security = Security()
            token = UsernameToken(self.username, self.password)
            security.tokens.append(token)
            self.client.set_options(wsse=security)

        dhl_shipment = self.create_dhl_shipment(self.client, shipment)

        result_code, reply = self.client.service.createShipmentRequest(message, None, dhl_shipment)

        try:
            identification_number = reply.ShipmentIdentificationNumber
            package_result = reply.PackagesResult.PackageResult[0]
            tracking_number = package_result.TrackingNumber

            try:
                dispatch_number = reply.DispatchConfirmationNumber

            except AttributeError:
                dispatch_number = None

            if reply.LabelImage[0].GraphicImage:
                label_bytes = reply.LabelImage[0].GraphicImage
                shipment.response = DHLResponse(
                    success=True,
                    tracking_number=tracking_number,
                    identification_number=identification_number,
                    label_bytes=label_bytes
                )

                print('Successfully created DHL shipment!')
                print('  Tracking number: ' + tracking_number)
                print('  Identification number: ' + identification_number)
                if dispatch_number:
                    shipment.response.dispatch_number = dispatch_number
                    print('  Dispatch number: ' + dispatch_number)
                print('  PDF label saved.')
                return True

            else:
                print('  No PDF label!')
        except AttributeError:
            print('Unsuccessful DHL shipment request.')
            shipment.response = DHLResponse(
                success=False
            )
            try:
                if reply.Notification:
                    print('  Notifications:')

                errors = []
                for notif in reply.Notification:
                    errors.append([notif._code, notif.Message])
                    print('  [Code: ' + notif._code + ', Message: ' + notif.Message + ']')
                shipment.response.errors = errors
            except AttributeError:
                print('  No notifications.')
        print()

        return False

    def create_dhl_shipment(self, client, shipment):
        """
        Creates a soap DHL shipment from the DHLShipment and the soap client.
        :param client: soap client
        :param shipment: DHLShipment object
        :return: soap dhl shipment
        """
        shipment.automatically_set_predictable_fields()

        dhl_shipment = client.factory.create('ns4:docTypeRef_RequestedShipmentType')
        dhl_shipment.ShipmentInfo.Currency = shipment.currency
        dhl_shipment.ShipmentInfo.UnitOfMeasurement = shipment.unit
        dhl_shipment.ShipmentInfo.LabelType = shipment.label_type
        dhl_shipment.ShipmentInfo.LabelTemplate = shipment.label_template
        dhl_shipment.ShipmentInfo.Account = self.account_number
        dhl_shipment.ShipmentInfo.PackagesCount = str(len(shipment.packages))
        dhl_shipment.PaymentInfo = shipment.payment_info
        dhl_shipment.ShipmentInfo.ServiceType = shipment.service_type
        dhl_shipment.InternationalDetail.Commodities.Description = shipment.customs_description
        dhl_shipment.InternationalDetail.Commodities.CustomsValue = shipment.customs_value
        dhl_shipment.InternationalDetail.Content = shipment.customs_content
        dhl_shipment.ShipmentInfo.DropOffType = shipment.drop_off_type
        dhl_shipment.ShipTimestamp = shipment.get_dhl_formatted_shipment_time()
        dhl_shipment.PickupLocationCloseTime = shipment.get_dhl_formatted_pickup_time()

        dhl_shipment.Ship.Shipper.Contact.PersonName = shipment.sender.person_name
        dhl_shipment.Ship.Shipper.Contact.CompanyName = shipment.sender.company_name
        dhl_shipment.Ship.Shipper.Contact.PhoneNumber = shipment.sender.phone
        dhl_shipment.Ship.Shipper.Contact.EmailAddress = shipment.sender.email
        dhl_shipment.Ship.Shipper.Address.StreetLines = shipment.sender.street_lines
        dhl_shipment.Ship.Shipper.Address.StreetLines2 = shipment.sender.street_lines2
        dhl_shipment.Ship.Shipper.Address.StreetLines3 = shipment.sender.street_lines3
        dhl_shipment.Ship.Shipper.Address.City = shipment.sender.city
        dhl_shipment.Ship.Shipper.Address.PostalCode = shipment.sender.postal_code
        dhl_shipment.Ship.Shipper.Address.CountryCode = shipment.sender.country_code

        dhl_shipment.Ship.Recipient.Contact.PersonName = shipment.receiver.person_name
        dhl_shipment.Ship.Recipient.Contact.CompanyName = shipment.receiver.company_name
        dhl_shipment.Ship.Recipient.Contact.PhoneNumber = shipment.receiver.phone
        dhl_shipment.Ship.Recipient.Contact.EmailAddress = shipment.receiver.email
        dhl_shipment.Ship.Recipient.Address.StreetLines = shipment.receiver.street_lines
        dhl_shipment.Ship.Recipient.Address.StreetLines2 = shipment.receiver.street_lines2
        dhl_shipment.Ship.Recipient.Address.StreetLines3 = shipment.receiver.street_lines3
        dhl_shipment.Ship.Recipient.Address.City = shipment.receiver.city
        dhl_shipment.Ship.Recipient.Address.PostalCode = shipment.receiver.postal_code
        dhl_shipment.Ship.Recipient.Address.CountryCode = shipment.receiver.country_code

        counter = 1
        dhl_shipment.Packages.RequestedPackages = ()
        for package in shipment.packages:
            dhl_package = client.factory.create('ns4:docTypeRef_RequestedPackagesType')
            dhl_package._number = str(counter)
            dhl_package.Weight = str(package.weight)
            dhl_package.Dimensions.Length = str(package.length)
            dhl_package.Dimensions.Width = str(package.width)
            dhl_package.Dimensions.Height = str(package.height)
            dhl_package.CustomerReferences = str('Test')

            dhl_shipment.Packages.RequestedPackages += (dhl_package,)
            counter += 1

        return dhl_shipment
