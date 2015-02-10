class DHLResponse:
    def __init__(self, success, errors=None):
        self.success = success
        self.errors = errors


class DHLShipmentResponse(DHLResponse):
    def __init__(self, success, tracking_numbers=None, identification_number=None, dispatch_number=None,
                 label_bytes=None, errors=None):
        DHLResponse.__init__(self, success, errors)

        self.tracking_numbers = tracking_numbers
        self.identification_number = identification_number
        self.dispatch_number = dispatch_number
        self.label_bytes = label_bytes


class DHLTrackingResponse(DHLResponse):
    def __init__(self, success, shipment_events=None, pieces_events=None, errors=None):
        DHLResponse.__init__(self, success, errors)

        self.shipment_events = shipment_events  # DHLTackingEvent
        self.pieces_events = pieces_events  # {tracking : [DHLTackingEvent...] ... }


class DHLPodResponse(DHLResponse):
    def __init__(self, success, pod_bytes=None, errors=None):
        DHLResponse.__init__(self, success, errors)

        self.pod_bytes = pod_bytes


class DHLTrackingEvent:
    def __init__(self, code=None, description=None, location_code=None, location_description=None, date=None,
                 time=None):
        self.date = date
        self.time = time
        self.code = code
        self.description = description
        self.location_code = location_code
        self.location_description = location_description