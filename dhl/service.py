from suds.client import Client
from suds.wsse import Security, UsernameToken

from dhl.resources.address import DHLPerson, DHLCompany
from dhl.resources.package import DHLPackage
from dhl.resources.shipment import DHLShipment
from dhl.resources.response import DHLShipmentResponse, DHLPodResponse, DHLTrackingResponse, DHLTrackingEvent


class DHLService:
    """
    Main class with static data and the main shipping methods.
    """
    shipment_test_url = 'https://wsb.dhl.com/sndpt/expressRateBook?wsdl'
    shipment_url = 'https://wsb.dhl.com:443/gbl/expressRateBook?wsdl'
    pod_test_url = 'https://wsb.dhl.com:443/sndpt/getePOD?WSDL'
    pod_url = 'https://wsb.dhl.com:443/gbl/getePOD?WSDL'
    tracking_test_url = 'https://wsb.dhl.com:443/sndpt/gblDHLExpressTrack?WSDL'
    tracking_url = 'https://wsb.dhl.com:443/gbl/glDHLExpressTrack?WSDL'


    def __init__(self, username, password, account_number, test_mode=False):
        self.username = username
        self.password = password
        self.account_number = account_number
        self.test_mode = test_mode
        self.shipment_client = None
        self.pod_client = None
        self.tracking_client = None

    def send(self, shipment, message=None):
        """
        Creates the client, the DHL shipment and makes the DHL web request.
        :param shipment: DHLShipment object
        :param message: optional message
        :return: DHLResponse
        """

        if not self.shipment_client:
            url = self.shipment_test_url if self.test_mode else self.shipment_url
            self.shipment_client = Client(url, faults=False)

            security = Security()
            token = UsernameToken(self.username, self.password)
            security.tokens.append(token)
            self.shipment_client.set_options(wsse=security)

        dhl_shipment = self._create_dhl_shipment(self.shipment_client, shipment)

        result_code, reply = self.shipment_client.service.createShipmentRequest(message, None, dhl_shipment)

        try:
            identification_number = reply.ShipmentIdentificationNumber
            package_results = reply.PackagesResult.PackageResult
            tracking_numbers = [result.TrackingNumber for result in package_results]

            try:
                dispatch_number = reply.DispatchConfirmationNumber

            except AttributeError:
                dispatch_number = None

            if reply.LabelImage[0].GraphicImage:
                label_bytes = reply.LabelImage[0].GraphicImage
                response = DHLShipmentResponse(
                    success=True,
                    tracking_numbers=tracking_numbers,
                    identification_number=identification_number,
                    label_bytes=label_bytes
                )

                print('Successfully created DHL shipment!')
                print('  Tracking numbers: ' + str(tracking_numbers))
                print('  Identification number: ' + identification_number)
                if dispatch_number:
                    response.dispatch_number = dispatch_number
                    print('  Dispatch number: ' + dispatch_number)
                print('  PDF label saved.')
                return response

            else:
                print('  No PDF label!')
                response = DHLShipmentResponse(
                    success=False,
                    errors=['No PDF label.']
                )
        except AttributeError:
            print('Unsuccessful DHL shipment request.')
            response = DHLShipmentResponse(
                success=False
            )
            try:
                if reply.Notification:
                    print('  Notifications:')

                errors = []
                for notif in reply.Notification:
                    errors.append([notif._code, notif.Message])
                    print('  [Code: ' + notif._code + ', Message: ' + notif.Message + ']')
                response.errors = errors
            except AttributeError:
                print('  No notifications.')
                response.errors = ['No notifications.']
        print()

        return response


    def proof_of_delivery(self, shipment_awb, detailed=True):
        """
        Connects to DHL ePOD service, and returns the POD for the requested shipment.
        :param shipment_awb: shipment waybill or identification number
        :param detailed: if a detailed POD should be returned, else simple
        :return: (True, pdf bytes) if successful else (False, [errors])
        """
        if not self.pod_client:
            url = self.pod_test_url if self.test_mode else self.pod_url
            self.pod_client = Client(url, faults=False)

            security = Security()
            token = UsernameToken(self.username, self.password)
            security.tokens.append(token)
            self.pod_client.set_options(wsse=security)

        msg = self._create_dhl_shipment_document(shipment_awb, detailed)
        code, res = self.pod_client.service.ShipmentDocumentRetrieve(msg)

        try:
            img = res.Bd.Shp[0].ShpInDoc[0].SDoc[0].Img[0]._Img
            return DHLPodResponse(True, img)
        except:
            return DHLPodResponse(False, errors=[error.DatErrMsg.ErrMsgDtl._DtlDsc for error in res.DatTrErr])

    def tracking(self, shipment_awb):
        if not self.tracking_client:
            url = self.tracking_test_url if self.test_mode else self.tracking_url
            self.tracking_client = Client(url, faults=False)

            security = Security()
            token = UsernameToken(self.username, self.password)
            security.tokens.append(token)
            self.tracking_client.set_options(wsse=security)

        tracking_request = self.tracking_client.factory.create('pubTrackingRequest')
        tracking_request.TrackingRequest.Request.ServiceHeader.MessageTime = '2015-02-09T18:00:00Z'
        tracking_request.TrackingRequest.Request.ServiceHeader.MessageReference = '123456789012345678901234567890'
        tracking_request.TrackingRequest.AWBNumber.ArrayOfAWBNumberItem = shipment_awb
        tracking_request.TrackingRequest.LevelOfDetails = 'ALL_CHECK_POINTS'
        tracking_request.TrackingRequest.PiecesEnabled = 'B'

        code, res = self.tracking_client.service.trackShipmentRequest(tracking_request)

        shipment_events = res.TrackingResponse.AWBInfo.ArrayOfAWBInfoItem[
            0].ShipmentInfo.ShipmentEvent.ArrayOfShipmentEventItem
        pieces = res.TrackingResponse.AWBInfo.ArrayOfAWBInfoItem[0].Pieces.PieceInfo.ArrayOfPieceInfoItem

        dhl_shipment_events = []
        for event in shipment_events:
            tracking_event = DHLTrackingEvent(
                code=event.ServiceEvent.EventCode,
                location_code=event.ServiceArea.ServiceAreaCode,
                location_description=event.ServiceArea.Description
            )
            dhl_shipment_events.append(tracking_event)

        dhl_pieces_events = {}
        for piece in pieces:
            tracking_number = piece.PieceDetails.LicensePlate
            dhl_pieces_events[tracking_number] = []
            for event in piece.PieceEvent.ArrayOfPieceEventItem:
                try:
                    dhl_pieces_events[tracking_number].append(
                        DHLTrackingEvent(
                            date=event.Date,
                            time=event.Time,
                            code=event.ServiceEvent.EventCode,
                            description=event.ServiceEvent.Description,
                            location_code=event.ServiceArea.ServiceAreaCode,
                            location_description=event.ServiceArea.Description
                        )
                    )
                except:
                    pass

        return DHLTrackingResponse(
            success=True,
            shipment_events=dhl_shipment_events,
            pieces_events=dhl_pieces_events
        )


    ########################################################################
    # PRIVATE METHODS ######################################################
    ########################################################################

    def _create_dhl_shipment_document(self, shipment_awb, detailed):
        """
        Creates the DHL request for POD retrieve.
        :param shipment_awb: shipment id
        :param detailed: if detailed or simple pod
        :return: message
        """
        msg = self.pod_client.factory.create('shipmentDocumentRetrieveReq').MSG

        msg.Hdr._Id = 'id'
        msg.Hdr._Ver = '1.038'
        msg.Hdr._Dtm = '2015-02-09T13:00:00'
        msg.Hdr.Sndr._AppCd = 'DCG'
        msg.Hdr.Sndr._AppNm = 'DCG'

        msg.Bd.Shp = self.pod_client.factory.create('ns4:CdmShipment_Shipment')
        msg.Bd.Shp._Id = str(shipment_awb)
        msg.Bd.Shp.ShpInDoc = self.pod_client.factory.create('ns5:CdmShipment_CustomsDocuments_ShipmentDocumentation')
        msg.Bd.Shp.ShpInDoc._DocTyCd = 'POD'
        msg.Bd.Shp.ShpTr = self.pod_client.factory.create('ns4:CdmShipment_ShipmentTransaction')
        msg.Bd.Shp.ShpTr.SCDtl = self.pod_client.factory.create('ns4:CdmShipment_ShipmentCustomerDetail')
        if detailed:
            msg.Bd.Shp.ShpTr.SCDtl._AccNo = self.account_number
            msg.Bd.Shp.ShpTr.SCDtl._CRlTyCd = 'SP'

        criterias = {
            'IMG_CONTENT': 'epod-detail' if detailed else 'epod-summary',
            'IMG_FORMAT': 'PDF',
            'DOC_RND_REQ': 'true',
            'EXT_REQ': 'true',
            'DUPL_HANDL': 'CORE_WB_NO',
            'SORT_BY': '$INGEST_DATE,D',
            'LANGUAGE': 'en'
        }
        msg.Bd.GenrcRq = self.pod_client.factory.create('ns2:CdmGenericRequest_GenericRequest')

        for key, value in criterias.items():
            criteria = self.pod_client.factory.create('ns2:CdmGenericRequest_GenericRequestCriteria')
            criteria._TyCd = key
            criteria._Val = value
            msg.Bd.GenrcRq.GenrcRqCritr += (criteria,)

        return msg


    def _create_dhl_shipment(self, client, shipment):
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
