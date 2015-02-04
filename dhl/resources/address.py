__author__ = 'Bench'


class DHLAddress:
    """
    Saves all the address data.
    """

    def __init__(self, street_lines, city, country_code, postal_code, street_lines2=None, street_lines3=None):
        self.street_lines = street_lines
        self.city = city
        self.country_code = country_code
        self.postal_code = postal_code
        self.street_lines2 = street_lines2
        self.street_lines3 = street_lines3


class DHLPerson(DHLAddress):
    """
    A class for creating the shipper and the recipient in the DHLShipment.
    """

    def __init__(self, person_name, street_lines, city, country_code, phone=None,
                 email=None, postal_code=None, street_lines2=None, street_lines3=None):
        DHLAddress.__init__(self, street_lines, city, country_code, postal_code, street_lines2, street_lines3)

        self.person_name = person_name
        self.phone = phone
        self.email = email
        self.company_name = person_name  # DHL requires the company name, so we use person name


class DHLCompany(DHLPerson):
    """
    A class for creating a company instead of a person for use in DHLShipment.
    """

    def __init__(self, company_name, person_name, street_lines, city, country_code, phone=None, email=None,
                 postal_code=None, street_lines2=None, street_lines3=None):
        DHLPerson.__init__(self, person_name, street_lines, city, country_code, phone, email, postal_code,
                           street_lines2, street_lines3)

        self.company_name = company_name

