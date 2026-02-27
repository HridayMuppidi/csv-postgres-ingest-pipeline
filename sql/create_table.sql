create table if not exists california_properties (
    primary_number varchar(50),
    otis_id varchar(50), --sometimes otis_id has trailing 0's, so we will keep it as varchar
    property_number varchar(50),
    name varchar(255),
    aliases_and_alias_types text, --aliases can be long, so we will keep it as text
    street_number varchar(50),
    street_name varchar(50),
    city varchar(50),
    county varchar(50),
    zip_code varchar(50), --sometimes zip has trailing 0's, so we will keep it as varchar
    vicinity varchar(50),
    other_geographical_indicators text, --other geographical indicators can be long, so we will keep it as text
    evaluation_information text, --evaluation information can be long, so we will keep it as text
    district_elements text, --district elements can be long, so we will keep it as text
    parent_district varchar(50),
    associated_resources text, --associated resources can be long, so we will keep it as text
    parcel_number varchar(50),
    mile_post varchar(50),
    ownership varchar(50),
    construction_years varchar(50), --since we have from and to years, we will keep it as varchar
    ocode varchar(50),
    date_modified date,
    export_date date,
    lastupdatedt timestamp,
    updateuser varchar(50),
    constraint pk_california_properties primary key (otis_id)
);
--creating an index on otis_id to improve query performance
create index if not exists idx_california_properties_otis_id on california_properties(otis_id);
