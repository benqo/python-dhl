# Python DHL

This is a python package for using the DHL webservices. 
It allows developers to easily connect to DHL services and make requests. 
The package creates SOAP requests useing the [suds-jurko](https://pypi.python.org/pypi/suds-jurko/0.6) package
to create shipments, schedule a pickup and possibliy to delete a created shipment.
It also provides the ability to save the shipping labels.

## Installation

Python DHL is available through pip. To easily install or upgrade it, do

    pip install --upgrade python-dhl

## Usage

To send a shipment you need to create:

1. The DHL service
2. The sender
3. The receiver
4. The packages
5. The shipment that connects the sender, receiver and the packages

And then use the DHL service to send the shipment.

### Create the DHL service

Initialize a new DHL service using

```python
service = DHLService('username', 'password', 'accountNumber')
``` 
You can also use the DHL test mode

```python
service.test_mode = True
``` 
     
### Create the sender

Sender can either be a ``DHLPerson`` or a ``DHLCompany``.

```python
sender = DHLCompany(
            company_name='GitHub',
            person_name='Git Hub',
            street_lines='275 Brannan Street',
            city='San Francisco,
            postal_code='94107',
            country_code='US',
            phone='11111111',
            email='git@github.com')
``` 
    
    
### Create the receiver

Receiver can also be either a ``DHLPerson`` or a ``DHLCompany``.

```python
receiver = DHLPerson(
            person_name='Jon Doe',
            street_lines='276 Brannan Street',
            city='San Francisco,
            postal_code='94107',
            country_code='US',
            phone='11111111',
            email='jon@github.com')
``` 
    
    
### Create the packages

The packages are ``DHLPackage`` objects and are supposed to be in a list.

```python
packages = [
    DHLPackage(
        weight=0.15,
        width=10,
        length=10,
        height=10,
        price=100,
        description='Good product'
    ),
    DHLPackage(
        weight=0.15,
        width=10,
        length=10,
        height=10,
        price=100,
        description='The best product'
    )
]
``` 
    
    
### Create the shipment

Shipment is a ``DHLShipment`` object and connects the sender, receiver and the packages.

```python
shipment = DHLShipment(sender, receiver, packages)
``` 
    
   
#### Request a pickup
If you wish to request a courier pickup, set
    
```python
shipment.drop_off_type = DHLShipment.DROP_OFF_REQUEST_COURIER
``` 
    

### Send the shipment

You are now ready to send the shipment. Simply call

```python
service.send(shipment)
``` 
    
Once the service is done, it stores the tracking number, identification number and the label in the ``shipment`` object.
It also saves the dispatch identification number in case a pickup was requested as well.

You can save the label to a file (by default to folder ``labels/``, you can change this by changing ``shipment.label_path``)

```python
shipment.save_label_to_file()
``` 
    
    
### Delete a shipment

TODO 
    
    How to delete