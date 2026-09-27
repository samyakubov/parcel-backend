ALTER TABLE real_property_legals ADD COLUMN IF NOT EXISTS bbl char(10);
UPDATE real_property_legals SET bbl = cast(borough as text) || lpad(cast(block as text), 5, '0') || lpad(cast(lot as text), 4, '0');

ALTER TABLE personal_property_legals ADD COLUMN IF NOT EXISTS bbl char(10);
UPDATE personal_property_legals SET bbl = cast(borough as text) || lpad(cast(block as text), 5, '0') || lpad(cast(lot as text), 4, '0');

CREATE INDEX IF NOT EXISTS real_property_legals_bbl_idx on real_property_legals (bbl);
CREATE INDEX IF NOT EXISTS personal_property_legals_bbl_idx on personal_property_legals (bbl);

CREATE INDEX IF NOT EXISTS real_property_legals_documentid_idx on real_property_legals(documentid);
CREATE INDEX IF NOT EXISTS real_property_master_documentid_idx on real_property_master(documentid);
CREATE INDEX IF NOT EXISTS real_property_parties_documentid_idx on real_property_parties(documentid);

CREATE INDEX IF NOT EXISTS personal_property_legals_documentid_idx on personal_property_legals(documentid);
CREATE INDEX IF NOT EXISTS personal_property_master_documentid_idx on personal_property_master(documentid);
CREATE INDEX IF NOT EXISTS personal_property_parties_documentid_idx on personal_property_parties(documentid);

CREATE INDEX IF NOT EXISTS real_property_master_doctype_idx on real_property_master(doctype);
CREATE INDEX IF NOT EXISTS real_property_master_docamount_idx on real_property_master(docamount);
CREATE INDEX IF NOT EXISTS real_property_master_docdate_idx on real_property_master(docdate);

CREATE INDEX IF NOT EXISTS real_property_parties_name_idx on real_property_parties(name);
CREATE INDEX IF NOT EXISTS real_property_parties_partytype_idx on real_property_parties(partytype);
