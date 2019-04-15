Issues
======

This page lists the possible issues that can occur when creating
channels and when sending data, and possible mitigation.

Control Layer
*************

Flow Request Creation
---------------------

+----------------------+----------+------------------------+-----------------------+------------------------+
| Issue                | Blocking | Effect                 | Mitigation            | Mitigation implemented |
+======================+==========+========================+=======================+========================+
|| Error in parameters | Yes      || The Flow Request      || Health Gateway       | No                     |
|                      |          || creation fails        || returns 400          |                        |
|                      |          ||                       ||                      |                        |
|                      |          ||                       ||                      |                        |
+----------------------+----------+------------------------+-----------------------+------------------------+

Flow Request Confirmation
-------------------------

+----------------------+----------+------------------------+-----------------------+------------------------+
| Issue                | Blocking | Effect                 | Mitigation            | Mitigation implemented |
+======================+==========+========================+=======================+========================+
|| Cannot contact IdP  | Yes      || The login into the    || Health Gateway       | No                     |
|                      |          || Health Gateway fails  || redirects to the     |                        |
|                      |          || and the confirmation  || destination with an  |                        |
|                      |          || process fails         || error feedback       |                        |
+----------------------+----------+------------------------+-----------------------+------------------------+
|| The person rejects  | Yes      || The Health Gateway    || Health Gateway       | No                     | 
|| authorization in    |          || cannot get patient's  || redirects to the     |                        |
|| the IdP             |          || demographics from IdP || destination with an  |                        |
||                     |          || and the process fails || error feedback       |                        |
+----------------------+----------+------------------------+-----------------------+------------------------+
|| Wrong parameters    | Yes      || The Health Gateway    || Health Gateway       | No                     |
|| in the request      |          || shows an error        || redirects to the     |                        |
||                     |          ||                       || destination with an  |                        |
||                     |          ||                       || error feedback       |                        |
+----------------------+----------+------------------------+-----------------------+------------------------+
|| Connection or oauth | Yes      || The Health Gateway    || Health Gateway       | No                     |
|| error with HGW      |          || cannot create the     || redirects to the     |                        |
|| Backend             |          || channels              || destination with an  |                        |
||                     |          ||                       || error feedback       |                        |
+----------------------+----------+------------------------+-----------------------+------------------------+

Consents Creation
-----------------

+----------------------+----------+------------------------+-----------------------+------------------------+
| Issue                | Blocking | Effect                 | Mitigation            | Mitigation implemented |
+======================+==========+========================+=======================+========================+
|| Error in parameters | Yes      || The consent creation  || Health Gateway       | No                     |
|                      |          || fails                 || should return an     |                        |
|                      |          ||                       || error feedback       |                        |
|                      |          ||                       || to the destination   |                        |
+----------------------+----------+------------------------+-----------------------+------------------------+
|| Connection or oauth | Yes      || The Health Gateway    || Health Gateway       | No                     |
|| error with Consent  |          || cannot create the     || redirects to the     |                        |
|| Manager             |          || channels              || destination with an  |                        |
||                     |          ||                       || error feedback       |                        |
+----------------------+----------+------------------------+-----------------------+------------------------+
|| All possible        | Yes      || The Health Gateway    || Health Gateway       | Yes                    |
|| consents have been  |          || cannot create the     || redirects to the     |                        |
|| already created     |          || channels              || destination with an  |                        |
||                     |          ||                       || error feedback       |                        |
+----------------------+----------+------------------------+-----------------------+------------------------+

Consents Confirmation
---------------------

+----------------------+----------+------------------------+-----------------------+------------------------+
| Issue                | Blocking | Effect                 | Mitigation            | Mitigation implemented |
+======================+==========+========================+=======================+========================+
|| Cannot contact IdP  | Yes      || The login into the    || Health Gateway       | No                     |
|                      |          || Consent Manager fails || redirects to the     |                        |
|                      |          || and the confirmation  || destination with an  |                        |
|                      |          || process fails         || error feedback       |                        |
+----------------------+----------+------------------------+-----------------------+------------------------+
|| The person rejects  | Yes      || The Consent Manager   || Health Gateway       | No                     | 
|| authorization in    |          || cannot get patient's  || redirects to the     |                        |
|| the IdP             |          || demographics from IdP || destination with an  |                        |
||                     |          || and the process fails || error feedback       |                        |
+----------------------+----------+------------------------+-----------------------+------------------------+
|| Wrong parameters    | Yes      || The Consent Manager   || Health Gateway       | No                     |
|| in the request      |          || shows an error        || redirects to the     |                        |
||                     |          ||                       || destination with an  |                        |
||                     |          ||                       || error feedback       |                        |
+----------------------+----------+------------------------+-----------------------+------------------------+
|| Kafka connection    | No       || The Consent Manager   || Consent Manager      | No                     |
|| error when sending  |          || fails to notify       || should retry to      |                        |
|| notification to the |          || the Health Gateway    || send the message     |                        |
|| topic               |          || about theconsents     || in the kafka topic   |                        |
+----------------------+----------+------------------------+-----------------------+------------------------+

Health Gateway Backend notification
-----------------------------------

+----------------------+----------+-------------------------+-----------------------+------------------------+
| Issue                | Blocking | Effect                  | Mitigation            | Mitigation implemented |
+======================+==========+=========================+=======================+========================+
|| Kafka connection    | No       || The HGW Frontend does  || HGW Frontend         | No                     |
|| error when sending  |          || not notify the backend || should retry to      |                        |
|| channels data in    |          || about the new channels || send the message     |                        |
|| the topic           |          || and sources cannot be  || in the kafka topic   |                        |
||                     |          || informed               ||                      |                        |
+----------------------+----------+-------------------------+-----------------------+------------------------+

Creation of connectors in the Source
------------------------------------

+----------------------+----------+-------------------------+-----------------------+------------------------+
| Issue                | Blocking | Effect                  | Mitigation            | Mitigation implemented |
+======================+==========+=========================+=======================+========================+
|| Connection to the   | No       || The Source Endpoint    || HGW backend          | No                     |
|| Source Endpoint     |          || will not be notified   || should retry to      |                        |
|| fails               |          || about the new data     || open the connector   |                        |
||                     |          || transfer to activate   ||                      |                        |
||                     |          ||                        ||                      |                        |
+----------------------+----------+-------------------------+-----------------------+------------------------+
|| Authentication to   | No       || The Source Endpoint    || Some kind of alert   | Yes                    |
|| the Source Endpoint |          || will not be notified   || should be            |                        |
|| fails               |          || about the new data     || implemented and auth |                        |
||                     |          || transfer to activate   || parameters should be |                        |
||                     |          ||                        || checked              |                        |
+----------------------+----------+-------------------------+-----------------------+------------------------+

Data Flow Layer
***************

Data sending to Health Gateway
------------------------------

Using Kafka Prdoucer
####################

+----------------------+----------+-------------------------+-----------------------+------------------------+
| Issue                | Blocking | Effect                  | Mitigation            | Mitigation implemented |
+======================+==========+=========================+=======================+========================+
|| Connection to the   | No       || The Source Endpoint    || The Source Endpoint  | No                     |
|| Kafka broker fails  |          || won't send the message || retries to send the  |                        |
||                     |          ||                        || message              |                        |
+----------------------+----------+-------------------------+-----------------------+------------------------+
|| Authentication to   | No       || The Source Endpoint    || The Source Endpoint  | Yes                    |
|| the Kafka broker    |          || won't send the message || retries to send the  |                        |
|| fails               |          ||                        || message              |                        |
+----------------------+----------+-------------------------+-----------------------+------------------------+

Using REST endpoint
###################

+----------------------+----------+-------------------------+-----------------------+------------------------+
| Issue                | Blocking | Effect                  | Mitigation            | Mitigation implemented |
+======================+==========+=========================+=======================+========================+
|| Connection to the   | No       || The Source Endpoint    || The Source Endpoint  | Must be implemented in |
|| HGW Backend fails   |          || won't send the message || retries to send the  | Source Endpoint        |
||                     |          ||                        || message              |                        |
+----------------------+----------+-------------------------+-----------------------+------------------------+
|| Authentication to   | No       || The Source Endpoint    || The Source Endpoint  | Must be implemented in |
|| the HGW Backend     |          || won't send the message || retries to send the  | Source Endpoint        |
|| broker fails        |          ||                        || message              |                        |
+----------------------+----------+-------------------------+-----------------------+------------------------+
|| Connection to the   | No       || The Source Endpoint    || The Source Endpoint  | Must be implemented in |
|| Kafka broker fails  |          || won't send the message || retries to send the  | Source Endpoint        |
||                     |          ||                        || message              |                        |
+----------------------+----------+-------------------------+-----------------------+------------------------+
|| Authentication to   | No       || The Source Endpoint    || The Source Endpoint  | Must be implemented in |
|| the Kafka broker    |          || won't send the message || retries to send the  | Source Endpoint        |
|| fails               |          ||                        || message              |                        |
+----------------------+----------+-------------------------+-----------------------+------------------------+
|| Message parameters  | No       || The Source Endpoint    || The Source Endpoint  | Must be implemented in |
|| are incorrect (e.g. |          || won't send the message || retries to send the  | Source Endpoint        |
|| unencrypted message |          ||                        || message              |                        |
+----------------------+----------+-------------------------+-----------------------+------------------------+
|| Message parameters  | No       || The Source Endpoint    || The Source Endpoint  | Must be implemented in |
|| are incorrect (e.g. |          || won't send the message || retries to send the  | Source Endpoint        |
|| unencrypted message |          ||                        || message              |                        |
+----------------------+----------+-------------------------+-----------------------+------------------------+

Data dispatching from Source Topic to Destination Topic
-------------------------------------------------------

Consuming from Source's Topic
#############################

+----------------------+----------+-------------------------+------------------------+------------------------+
| Issue                | Blocking | Effect                  | Mitigation             | Mitigation implemented |
+======================+==========+=========================+========================+========================+
|| Missing channel id  | Yes      || The message is lost    || TBD                   | No                     |
|| in kafka message    |          ||                        ||                       |                        |
+----------------------+----------+-------------------------+------------------------+------------------------+
|| Consent Manager is  | Yes      || The consent associated || Message must be       | No                     |
|| unreachable         |          || to the message cannot  || reprocessed           |                        |
||                     |          || be verified            ||                       |                        |
+----------------------+----------+-------------------------+------------------------+------------------------+
|| Consent Manager     | Yes      || The consent associated || Message must be       | No                     |
|| auth fails          |          || to the message cannot  || reprocessed           |                        |
||                     |          || be verified            ||                       |                        |
+----------------------+----------+-------------------------+------------------------+------------------------+
|| Consent is revoked  | Yes      || The message is not     || We should save the    |                        |
|| or expired          |          || dispatched             || message to understand |                        |
||                     |          ||                        || why it was sent by    |                        |
||                     |          ||                        || source                |                        |
+----------------------+----------+-------------------------+------------------------+------------------------+
|| HGW Frontend        | Yes      || We cannot discover the || Message must be       | No                     |
|| unreachable         |          || flow request           || reprocessed           |                        |
||                     |          || associated to the      ||                       |                        |
||                     |          || consent                ||                       |                        |
+----------------------+----------+-------------------------+------------------------+------------------------+
|| HGW Frontend        | Yes      || We cannot discover the || Message must be       | No                     |
|| auth fails          |          || flow request           || reprocessed           |                        |
||                     |          || associated to the      ||                       |                        |
||                     |          || consent                ||                       |                        |
+----------------------+----------+-------------------------+------------------------+------------------------+
|| The flow request    | Yes      || We cannot discover the || Message must be       | No                     |
|| corresponding to    |          || flow request           || reprocessed           |                        |
|| the channel is not  |          || associated to the      ||                       |                        |
|| found               |          || consent                ||                       |                        |
+----------------------+----------+-------------------------+------------------------+------------------------+

Delivering to the Destination's Topic
#####################################

+----------------------+----------+-------------------------+-----------------------+------------------------+
| Issue                | Blocking | Effect                  | Mitigation            | Mitigation implemented |
+======================+==========+=========================+=======================+========================+
|| The broker is       | Yes      || The message cannot be  || Message must be      | No                     |
|| unreachable         |          || dispatched             || reprocessed          |                        |
+----------------------+----------+-------------------------+-----------------------+------------------------+
|| The authentication  | Yes      || The message cannot be  || Message must be      | No                     |
|| to the broker fails |          || dispatched             || reprocessed          |                        |
+----------------------+----------+-------------------------+-----------------------+------------------------+
