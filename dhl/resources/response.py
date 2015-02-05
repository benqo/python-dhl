class DHLResponse:
    def __init__(self, success, tracking_number=None, identification_number=None, dispatch_number=None,
                 label_bytes=None, errors=None):
        self.success = success
        self.tracking_number = tracking_number
        self.identification_number = identification_number
        self.dispatch_number = dispatch_number
        self.label_bytes = label_bytes
        self.errors = errors