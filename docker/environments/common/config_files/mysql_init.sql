CREATE DATABASE IF NOT EXISTS `consentmanager`;
CREATE DATABASE IF NOT EXISTS `hgwfrontend`;
CREATE DATABASE IF NOT EXISTS `hgwbackend`;

GRANT ALL ON consentmanager.* TO 'hgwuser'@'%';
GRANT ALL ON hgwfrontend.* TO 'hgwuser'@'%';
GRANT ALL ON hgwbackend.* TO 'hgwuser'@'%';