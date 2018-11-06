# Copyright (c) 2017-2018 CRS4
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


FROM italia/spid-testenv-identityserver:docker-compose

ADD WSO2CARBON_DB.h2.db /spid-testenvironment/is/identity-server/repository/database/WSO2CARBON_DB.h2.db
ADD wso2carbon.jks /spid-testenvironment/is/identity-server/repository/resources/security/wso2carbon.jks
ADD client-truststore.jks /spid-testenvironment/is/identity-server/repository/resources/security/client-truststore.jks
USER root
RUN chown yoda:yoda /spid-testenvironment/is/identity-server/repository/database/WSO2CARBON_DB.h2.db
RUN chmod 664 /spid-testenvironment/is/identity-server/repository/database/WSO2CARBON_DB.h2.db
RUN chown yoda:yoda /spid-testenvironment/is/identity-server/repository/resources/security/wso2carbon.jks
RUN chmod 664 /spid-testenvironment/is/identity-server/repository/resources/security/wso2carbon.jks
RUN chown yoda:yoda /spid-testenvironment/is/identity-server/repository/resources/security/client-truststore.jks
RUN chmod 664 /spid-testenvironment/is/identity-server/repository/resources/security/client-truststore.jks
USER yoda