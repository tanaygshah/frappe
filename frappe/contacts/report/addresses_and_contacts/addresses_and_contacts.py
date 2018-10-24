# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from six.moves import range
from six import iteritems
import frappe


field_map = {
	"Contact": [ "first_name", "last_name", "phone", "mobile_no", "email_id", "is_primary_contact" ],
	"Address": [ "address_line1", "address_line2", "city", "state", "pincode", "country", "is_primary_address" ]
}

def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_columns(filters):
	return [
		"{reference_doctype}:Link/{reference_doctype}".format(reference_doctype=filters.get("reference_doctype")),
		"Address Line 1",
		"Address Line 2",
		"City",
		"State",
		"Postal Code",
		"Country",
		"Is Primary Address:Check",
		"First Name",
		"Last Name",
		"Phone",
		"Mobile No",
		"Email Id",
		"Is Primary Contact:Check"
	]

def get_data(filters):
	data = []
	reference_doctype = filters.get("reference_doctype")
	reference_name = filters.get("reference_name")

	return get_reference_addresses_and_contact(reference_doctype, reference_name)

def get_reference_addresses_and_contact(reference_doctype, reference_name):
	data = []
	filters = None
	reference_details = frappe._dict()

	if not reference_doctype:
		return []

	if reference_name:
		filters = { "name": reference_name }

	reference_list = [d[0] for d in frappe.get_list(reference_doctype, filters=filters, fields=["name"], as_list=True)]
	for d in reference_list:
		reference_details.setdefault(d, frappe._dict())

	reference_details = get_reference_details(reference_doctype, reference_list, "Address", reference_details)
	reference_details = get_reference_details(reference_doctype, reference_list, "Contact", reference_details)

	for reference_name, details in iteritems(reference_details):
		addresses = details.get("address", [])
		contacts  = details.get("contact", [])
		if not any([addresses, contacts]):
			result = [reference_name]
			result.extend(add_blank_columns_for("Contact"))
			result.extend(add_blank_columns_for("Address"))
			data.append(result)
		else:
			addresses = map(list, addresses)
			contacts = map(list, contacts)

			max_length = max(len(addresses), len(contacts))
			for idx in range(0, max_length):
				result = [reference_name]
				address = addresses[idx] if idx < len(addresses) else add_blank_columns_for("Address")
				contact = contacts[idx] if idx < len(contacts) else add_blank_columns_for("Contact")
				result.extend(address)
				result.extend(contact)

				data.append(result)
	return data

def get_reference_details(reference_doctype, reference_list, doctype, reference_details):
	filters =  [
		["Dynamic Link", "link_doctype", "=", reference_doctype],
		["Dynamic Link", "link_name", "in", reference_list]
	]
	fields = ["`tabDynamic Link`.link_name"] + field_map.get(doctype, [])

	records = frappe.get_list(doctype, filters=filters, fields=fields, as_list=True)
	for d in records:
		details = reference_details.get(d[0]) or {}
		details.setdefault(frappe.scrub(doctype), []).append(d[1:])

	return reference_details

def add_blank_columns_for(doctype):
	return ["" for field in field_map.get(doctype, [])]
