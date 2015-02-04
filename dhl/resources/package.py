class DHLPackage:
    """
    A class for creating separate packages contained in a shipment.
    """

    def __init__(self, weight, length, width, height, price=None, description=None):
        self.weight = weight  # kg
        self.length = length  # cm
        self.width = width  # cm
        self.height = height  # cm
        self.price = price
        self.description = description
