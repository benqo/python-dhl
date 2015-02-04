from datetime import datetime, timedelta


class DHLShipment:
    """
    A class for creating separate shipments.
    """

    DROP_OFF_REGULAR_PICKUP = 'REGULAR_PICKUP'
    DROP_OFF_REQUEST_COURIER = 'REQUEST_COURIER'

    SERVICE_TYPE_EU = 'U'
    SERVICE_TYPE_WORLD = 'P'
    SERVICE_TYPE_DOMESTIC = 'N'

    CURRENCY_EUR = 'EUR'
    CURRENCY_USD = 'USD'

    UNIT_METRIC = 'SI'
    UNIT_IMPERIAL = 'SU'

    CUSTOMS_PAYMENT_CLIENT = 'DDU'
    CUSTOMS_PAYMENT_CUSTOMER = 'DDP'

    CUSTOMS_DOCUMENTS = 'DOCUMENTS'
    CUSTOMS_NON_DOCUMENTS = 'NON_DOCUMENTS'

    label_type = 'PDF'
    label_template = 'ECOM26_84_001'

    def __init__(self, sender, receiver, packages, ship_datetime=datetime.now(), drop_off_type=DROP_OFF_REGULAR_PICKUP,
                 service_type=SERVICE_TYPE_EU, currency=CURRENCY_EUR, unit=UNIT_METRIC,
                 payment_info=CUSTOMS_PAYMENT_CLIENT, customs_description=None, customs_value=None, customs_content=CUSTOMS_NON_DOCUMENTS,
                 pickup_time=datetime.now()):
        self.sender = sender
        self.receiver = receiver
        self.packages = packages
        self.ship_datetime = ship_datetime
        self.drop_off_type = drop_off_type
        self.service_type = service_type
        self.currency = currency
        self.unit = unit
        self.payment_info = payment_info
        self.customs_description = customs_description
        self.customs_content = customs_content
        self.customs_value = customs_value
        self.pickup_time = pickup_time
        self.manifested = False
        self.labels_path = 'labels/'
        self.tracking_number = None
        self.identification_number = None
        self.label_bytes = None
        self.dispatch_number = None

    def manifest(self, tracking_number, identification_number, label_bytes, dispatch_number=None):
        self.tracking_number = tracking_number
        self.identification_number = identification_number
        self.label_bytes = label_bytes
        self.dispatch_number = dispatch_number
        if self.label_bytes:
            self.manifested = True

    def save_label_to_file(self):
        import os.path
        import base64

        if self.manifested:
            pdf_decoded = base64.b64decode(self.label_bytes)

            if not os.path.exists(self.labels_path):
                os.makedirs(self.labels_path)

            f = open(self.labels_path + self.tracking_number + '.PDF', 'wb')
            f.write(pdf_decoded)
            f.close()
        else:
            print('The shipment has not yet been sent to DHL service and it does not have a label.')