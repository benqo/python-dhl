from suds.client import Client
from suds.wsse import Security, UsernameToken
from datetime import timedelta
import time

from dhl.resources.address import DHLPerson, DHLCompany
from dhl.resources.package import DHLPackage
from dhl.resources.shipment import DHLShipment


class DHLService:
    """
    Main class with static data and the main shipping methods.
    """
    test_url = 'https://wsb.dhl.com/sndpt/expressRateBook?wsdl'
    url = 'https://wsb.dhl.com:443/gbl/expressRateBook?wsdl'
    dhl_datetime_format = "%Y-%m-%dT%H:%M:00 GMT"
    dhl_time_format = "%H:%M"
    utc_offset = None
    eu_codes = ("AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IT", "LV", "LI", "LT",
                "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE", "GB")

    def __init__(self, username, password, account_number, test_mode=False):
        self.username = username
        self.password = password
        self.account_number = account_number
        self.test_mode = test_mode
        self.client = None

    def send(self, shipment, message=None):
        if shipment.manifested:
            print('This shipment has already been sent. Please create a new shipment.')
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
                shipment.manifest(tracking_number, identification_number, label_bytes, dispatch_number=dispatch_number)

                print('Successfully created DHL shipment!')
                print('  Tracking number: ' + tracking_number)
                print('  Identification number: ' + identification_number)
                if dispatch_number:
                    print('  Dispatch number: ' + dispatch_number)
                print('  PDF label saved.')

            else:
                print('  No PDF label!')
        except AttributeError:
            print('Unsuccessful DHL shipment request.')
            try:
                if reply.Notification: print('  Notifications:')
                for notif in reply.Notification:
                    print('  [Code: ' + notif._code + ', Message: ' + notif.Message + ']')
            except AttributeError:
                print('  No notifications.')
        print()

    def create_dhl_shipment(self, client, shipment):
        dhl_shipment = client.factory.create('ns4:docTypeRef_RequestedShipmentType')
        dhl_shipment.ShipmentInfo.Currency = shipment.currency
        dhl_shipment.ShipmentInfo.UnitOfMeasurement = shipment.unit
        dhl_shipment.ShipmentInfo.LabelType = shipment.label_type
        dhl_shipment.ShipmentInfo.LabelTemplate = shipment.label_template
        dhl_shipment.ShipmentInfo.Account = self.account_number
        dhl_shipment.ShipmentInfo.PackagesCount = str(len(shipment.packages))
        dhl_shipment.PaymentInfo = shipment.payment_info

        dhl_shipment.ShipmentInfo.ServiceType = self.get_service_type(shipment)

        customs_description, customs_value = self.get_customs_description_and_value(shipment)

        dhl_shipment.InternationalDetail.Commodities.Description = customs_description
        dhl_shipment.InternationalDetail.Commodities.CustomsValue = customs_value

        dhl_shipment.InternationalDetail.Content = shipment.customs_content

        dhl_shipment.ShipTimestamp = self.get_dhl_formatted_shipment_time(shipment.ship_datetime)

        if shipment.request_pickup:
            dhl_shipment.ShipmentInfo.DropOffType = DHLShipment.DROP_OFF_REQUEST_COURIER
            dhl_shipment.PickupLocationCloseTime = self.get_dhl_formatted_pickup_time(shipment.pickup_time)
        else:
            dhl_shipment.ShipmentInfo.DropOffType = DHLShipment.DROP_OFF_REGULAR_PICKUP

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

    def get_dhl_formatted_shipment_time(self, datetime_stamp):
        if not self.utc_offset:
            # time lib https://docs.python.org/3/library/time.html#time.strftime
            self.utc_offset = time.strftime('%z')  # just take the utc offset from the time lib
            self.utc_offset = self.utc_offset[:-2] + ':' + self.utc_offset[-2:]  # insert : in +0100 to get +01:00

        datetime_stamp += timedelta(minutes=5)
        formatted_time = datetime_stamp.strftime(self.dhl_datetime_format)
        return formatted_time + self.utc_offset

    def get_dhl_formatted_pickup_time(self, datetime_stamp):
        datetime_stamp += timedelta(minutes=5)
        formatted_time = datetime_stamp.strftime(self.dhl_time_format)
        return formatted_time

    def get_customs_description_and_value(self, shipment):
        customs_description = ''
        customs_value = 0
        for package in shipment.packages:  # automatically generate description and value for customs
            customs_description += package.description + ", "
            customs_value += package.price

        # if the customs variables are not set, use the generated ones
        customs_description = shipment.customs_description if shipment.customs_description else customs_description[:-2]
        customs_value = shipment.customs_value if shipment.customs_value else customs_value

        return customs_description, customs_value

    def get_service_type(self, shipment):
        sender_code = shipment.sender.country_code
        receiver_code = shipment.receiver.country_code

        if sender_code == receiver_code:  # domestic
            return DHLShipment.SERVICE_TYPE_DOMESTIC
        elif sender_code in self.eu_codes and receiver_code in self.eu_codes:  # in EU
            return DHLShipment.SERVICE_TYPE_EU
        else:  # world
            return DHLShipment.SERVICE_TYPE_WORLD