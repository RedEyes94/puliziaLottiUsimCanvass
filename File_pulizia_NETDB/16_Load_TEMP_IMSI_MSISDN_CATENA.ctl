LOAD DATA
INFILE *
BADFILE './16_Load_TEMP_IMSI_MSISDN_3C.BAD'
DISCARDFILE './16_Load_TEMP_IMSI_MSISDN_3C.DSC'
APPEND INTO TABLE NETDBOWN.TEMP_IMSI_MSISDN
Fields terminated by ";" Optionally enclosed by '"'
(
  MSISDN,
  IMSI
)
BEGINDATA