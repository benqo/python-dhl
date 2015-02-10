from datetime import datetime, timedelta
import time


class DHLShipment:
    """
    A class for creating separate shipments.
    """

    DROP_OFF_REGULAR_PICKUP = 'REGULAR_PICKUP'
    DROP_OFF_REQUEST_COURIER = 'REQUEST_COURIER'

    SERVICE_TYPE_EU = 'U'
    SERVICE_TYPE_WORLD = 'P'
    SERVICE_TYPE_WORLD_DOCUMENTS = 'D'
    SERVICE_TYPE_DOMESTIC = 'N'

    CURRENCY_EUR = 'EUR'
    CURRENCY_USD = 'USD'

    UNIT_METRIC = 'SI'
    UNIT_IMPERIAL = 'SU'

    CUSTOMS_PAYMENT_CLIENT = 'DDU'
    CUSTOMS_PAYMENT_CUSTOMER = 'DAP'

    CUSTOMS_DOCUMENTS = 'DOCUMENTS'
    CUSTOMS_NON_DOCUMENTS = 'NON_DOCUMENTS'

    label_type = 'PDF'
    label_template = 'ECOM26_84_001'

    dhl_datetime_format = "%Y-%m-%dT%H:%M:%S GMT"
    dhl_time_format = "%H:%M"
    utc_offset = None
    eu_codes = ("AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IT", "LV", "LI", "LT",
                "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE", "GB")

    def __init__(self, sender, receiver, packages, ship_datetime=None, request_pickup=False,
                 service_type=SERVICE_TYPE_EU, currency=CURRENCY_EUR, unit=UNIT_METRIC,
                 payment_info=CUSTOMS_PAYMENT_CUSTOMER, customs_description=None, customs_value=None,
                 customs_content=CUSTOMS_NON_DOCUMENTS,
                 pickup_time=None):
        self.sender = sender
        self.receiver = receiver
        self.packages = packages
        self.ship_datetime = ship_datetime
        self.request_pickup = request_pickup
        self.service_type = service_type
        self.currency = currency
        self.unit = unit
        self.payment_info = payment_info
        self.customs_description = customs_description
        self.customs_content = customs_content
        self.customs_value = customs_value
        self.pickup_time = pickup_time
        self.drop_off_type = None
        self.labels_path = 'labels/'

    def automatically_set_predictable_fields(self):
        """
        Sets the shipment fields that are calculated/predicted from other fields.
        :return:
        """
        self.service_type = self.get_service_type()
        self.customs_description, self.customs_value = self.get_customs_description_and_value()
        self.drop_off_type = self.get_drop_off_type()
        self.pickup_time = self.get_pickup_time()

    def get_pickup_time(self):
        """
        Returns the correct pickup time, if the courier pickup is request, else None.
        :return: the correct pickup time, if the courier pickup is request, else None
        """
        if self.request_pickup:
            return self.pickup_time or datetime.now() + timedelta(hours=1)
        return None

    def get_drop_off_type(self):
        """
        Returns the drop off type.
        :return: the drop off type
        """
        return self.DROP_OFF_REQUEST_COURIER if self.request_pickup else self.DROP_OFF_REGULAR_PICKUP


    def get_dhl_formatted_shipment_time(self):
        """
        Formats the shipment date and time in the DHL time format, including the UTC offset
        :return: formatted date time stamp
        """
        self.ship_datetime = self.ship_datetime or datetime.now()
        if not self.utc_offset:
            # time lib https://docs.python.org/3/library/time.html#time.strftime
            self.utc_offset = time.strftime('%z')  # just take the utc offset from the time lib
            self.utc_offset = self.utc_offset[:-2] + ':' + self.utc_offset[-2:]  # insert : in +0100 to get +01:00

        self.ship_datetime += timedelta(minutes=5)
        formatted_time = self.ship_datetime.strftime(self.dhl_datetime_format)
        return formatted_time + self.utc_offset


    def get_dhl_formatted_pickup_time(self):
        """
        Formats the shipment pickup time.
        :return: formatted pickup time
        """
        if self.pickup_time:
            self.pickup_time += timedelta(minutes=5)
            formatted_time = self.pickup_time.strftime(self.dhl_time_format)
            return formatted_time
        return None


    def get_customs_description_and_value(self):
        """
        Generates the customs description, by concatenating the product description. Calculates the customs value by
        summarizing the product values.
        :return: customs description, customs value
        """
        customs_description = ''
        customs_value = 0
        for package in self.packages:  # automatically generate description and value for customs
            customs_description += package.description + ", "
            customs_value += package.price

        # if the customs variables are not set, use the generated ones
        customs_description = self.customs_description or customs_description[:-2]
        customs_value = self.customs_value or customs_value

        return customs_description, customs_value

    def get_service_type(self):
        """
        Returns the DHL service type, based on the country code of the sender, and the receiver.
        :return: dhl service type
        """
        sender_code = self.sender.country_code
        receiver_code = self.receiver.country_code

        if sender_code == receiver_code:  # domestic
            return DHLShipment.SERVICE_TYPE_DOMESTIC
        elif sender_code in self.eu_codes and receiver_code in self.eu_codes:  # in EU
            return DHLShipment.SERVICE_TYPE_EU
        else:  # world
            if self.customs_content == DHLShipment.CUSTOMS_DOCUMENTS:
                return DHLShipment.SERVICE_TYPE_WORLD_DOCUMENTS
            else:
                return DHLShipment.SERVICE_TYPE_WORLD


    #
    def save_label_to_file(self, label_bytes):
        """
        Saves the shipment label in bytes to a PDF file on disk.
        :return:
        """
        import os.path
        import base64

        pdf_decoded = base64.b64decode(self.response.label_bytes)

        if not os.path.exists(self.labels_path):
            os.makedirs(self.labels_path)

        f = open(self.labels_path + self.response.tracking_number + '.PDF', 'wb')
        f.write(pdf_decoded)
        f.close()