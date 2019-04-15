Issues
======

This page lists the possible issues that can occur when creating
channels and when sending data, and possible mitigation.

Control Layer
*************

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
|| Connection or oauth | Yes      || The Health Gateway    || Health Gateway       | No                     |
|| error with Consent  |          || cannot create the     || redirects to the     |                        |
|| Manager             |          || channels              || destination with an  |                        |
||                     |          ||                       || error feedback       |                        |
+----------------------+----------+------------------------+-----------------------+------------------------+