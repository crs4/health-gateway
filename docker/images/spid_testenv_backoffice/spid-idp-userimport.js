const axios = require("axios");
const soap = require('soap');
const fs = require('fs');
process.env['NODE_TLS_REJECT_UNAUTHORIZED'] = '0';



var config = {
	"wso2_url"		: "https://spid-testenv-identityserver:9443",
	"wso2_user"		: "admin",
	"wso2_pass" 	: "admin"
};


var users = [];

console.log("\nSPID User import");

process.stdout.write("\nLoading configuration... ");
readConfig();
process.stdout.write("Ok\n\n");
process.stdout.write("wso2_url: " + config.wso2_url + "\n");
process.stdout.write("wso2_user: " + config.wso2_user + "\n");
process.stdout.write("wso2_pass: " + config.wso2_pass + "\n\n");


var basicAuthSecurity = new soap.BasicAuthSecurity(config.wso2_user, config.wso2_pass);

process.stdout.write("# users imported: --");

function callback(data) {
    console.log(data.message);
}

// function ping() {
//     //dummy call only for check status
//     axios.get('https://localhost:8080/user?applicationName=PING')
//     .then(function (response) {
//         console.log(response);
//             getRoleNames({},
//                 (roles)=>{
//                     if(roles.indexOf("PUBLIC")!=-1) {
//                         addUsers(users, callback);
//                     } else {
//                         addRole(
//                             {roleName: "PUBLIC"},
//                             ()=> { addUsers(users, callback) },
//                             ()=> {
//                                 callback({
//                                     code: 400,
//                                     message: "Error while creating role PUBLIC on WSO2"
//                                 })}
//                         )
//                     }
//                 },
//                 ()=>{
//                     callback({
//                         code: 400,
//                         message: "Error while retrieving roles from WSO2"
//                     })}
//             );
//     })
//     .catch(function (error) {
//             ping();
//     });
// }

getRoleNames({},
    (roles)=>{
        if(roles.indexOf("PUBLIC")!=-1) {
            addUsers(users, callback);
        } else {
            addRole(
                {roleName: "PUBLIC"},
                ()=> { addUsers(users, callback) },
                ()=> {
                    callback({
                        code: 400,
                        message: "Error while creating role PUBLIC on WSO2"
                    })}
            )
        }
    },
    ()=>{
        callback({
            code: 400,
            message: "Error while retrieving roles from WSO2"
        })}
);

// for(i in users) {
// 	importUser(users[i], (result)=> {
// 		if(result.code==200) {
// 			process.stdout.write("\b\b" + ("00" + (+i+1)).slice(-2));
// 		} else {
// 			console.log("Error");
// 			console.log(result);
// 		}
// 	});
// }

// -----------------------------------------------------------------------------------------------------------

function readConfig() {
	try {
		users = JSON.parse(fs.readFileSync("spid-users.json"));
		config = JSON.parse(fs.readFileSync("spid-userimport-env"));
	} catch(e) {
		console.log("ERROR\n");
		console.log(e);
		process.exit();
	}

}

function help() {
	console.log("\nImport users into WSO2 IS");
	console.log("\nUsage: spid-testenv-user-import USERS_FILE OPTIONS_FILE");
	console.log("\nMandatory arguments:");
	console.log("   USERS_FILE\t\tJson file with data of users to import");
	console.log("   OPTIONS_FILE\t\tJson file with params of WSO2 Identity Server\n");
}


function getRoleNames(data, next, nexterr) {
	var url = config.wso2_url + '/services/RemoteUserStoreManagerService?wsdl';
	soap.createClient(url, function(err, client, raw) {
		if(client==null) { getRoleNames(data, next, nexterr); return; }
		if(raw!=null && (raw.indexOf("<faultstring>")>-1)) { nexterr(raw); return; }
		else {
			client.setSecurity(basicAuthSecurity);

			var args = {};

			client.getRoleNames(args, function(err, result, raw) {
				if(raw!=null && (raw.indexOf("<faultstring>")>-1)) { nexterr(raw); return; }
				else {
					if(result!=null && result.getRoleNamesResponse!=null) {
						next(result.getRoleNamesResponse.return);
					} else {
						nexterr();
					}
				}
			});
		}
	});
}


function addRole(data, next, nexterr) {
	var url = config.wso2_url + '/services/RemoteUserStoreManagerService?wsdl';
	soap.createClient(url, function(err, client, raw) {
		if(client==null) { nexterr("Identity Server not available"); return; }
		if(raw!=null && (raw.indexOf("<faultstring>")>-1)) { nexterr(parseFaultString(raw)); return; }
		else {
			client.setSecurity(basicAuthSecurity);

			var args = {
				roleName: data.roleName
			};

			client.addRole(args, function(err, result, raw) {
				if(raw!=null && (raw.indexOf("<faultstring>")>-1)) { nexterr(parseFaultString(raw)); return; }
				else { next(); }
			});
		}
	});
}


function addUsers(users, callback) {
	if(users.length>0) {
		let n = 0;
		for(i in users) {
			importUser(users[i], (result)=> {
				if(++n==users.length) {
					if(result.code==200) {
						callback({
							code: 200,
							message: result.message
						});
					} else {
						callback({
							code: 400,
							message: result.message
						});
					}
				}
			});
		}
	} else {
		callback({
			code: 404,
			message: "No test users found to import"
		});
	}
}


function importUser(user, callback) {

	res = false;

	addUser({
		"userName": user.userName,
		"lastName": user.lastName,
		"credential": user.credential,
		"roleList": user.roleList

	}, () => {

		var claimsSavedNum = 0;

		claimsSavedNum = checkLasteAddedUserClaimValue(user.userName, "http://wso2.org/claims/privatePersonalIdentifier", user.idCard, claimsSavedNum, callback);
		claimsSavedNum = checkLasteAddedUserClaimValue(user.userName, "http://wso2.org/claims/nickname", user.fiscalNumber, claimsSavedNum, callback);
		claimsSavedNum = checkLasteAddedUserClaimValue(user.userName, "http://wso2.org/claims/mobile", user.mobilePhone, claimsSavedNum, callback);
		claimsSavedNum = checkLasteAddedUserClaimValue(user.userName, "http://wso2.org/claims/dob", user.dateOfBirth, claimsSavedNum, callback);
		claimsSavedNum = checkLasteAddedUserClaimValue(user.userName, "http://wso2.org/claims/stateorprovince", user.countyOfBirth, claimsSavedNum, callback);
		claimsSavedNum = checkLasteAddedUserClaimValue(user.userName, "http://wso2.org/claims/givenname", user.name, claimsSavedNum, callback);
		claimsSavedNum = checkLasteAddedUserClaimValue(user.userName, "http://wso2.org/claims/otheremail", user.digitalAddress, claimsSavedNum, callback);
		claimsSavedNum = checkLasteAddedUserClaimValue(user.userName, "http://wso2.org/claims/im", user.ivaCode, claimsSavedNum, callback);
		claimsSavedNum = checkLasteAddedUserClaimValue(user.userName, "http://wso2.org/claims/locality", user.placeOfBirth, claimsSavedNum, callback);
		claimsSavedNum = checkLasteAddedUserClaimValue(user.userName, "http://wso2.org/claims/expirationdate", user.expirationDate, claimsSavedNum, callback);
		claimsSavedNum = checkLasteAddedUserClaimValue(user.userName, "http://wso2.org/claims/gender", user.gender, claimsSavedNum, callback);
		claimsSavedNum = checkLasteAddedUserClaimValue(user.userName, "http://wso2.org/claims/registeredOffice", user.registeredOffice, claimsSavedNum, callback);
		/* avoid saving username double
		  * claimsSavedNum = checkLasteAddedUserClaimValue(user.userName, "http://wso2.org/claims/lastname", user.familyName, claimsSavedNum, callback);
		*/
		claimsSavedNum = checkLasteAddedUserClaimValue(user.userName, "http://wso2.org/claims/emailaddress", user.email, claimsSavedNum, callback);
		claimsSavedNum = checkLasteAddedUserClaimValue(user.userName, "http://wso2.org/claims/organization", user.companyName, claimsSavedNum, callback);

		res = true;

	}, (errString) => {

		console.log("ERROR: " + errString);
		res = false;
	});

	return res;
}

function checkLasteAddedUserClaimValue(username, claimURI, remoteClaim, savedNum, callback) {
	savedNum++;

	addUserClaimValue({
		userName: username,
		claimURI: claimURI,
		value: remoteClaim
	}, () => {
			if(savedNum==14) {
				callback({
					code: 200,
					message: "Ok"
				});
			}
		}
	);
	return savedNum;
}

function addUser(data, next, nexterr) {
	var url = config.wso2_url + '/services/RemoteUserStoreManagerService?wsdl';
	soap.createClient(url, function(err, client, raw) {
		if(client==null) { nexterr("Identity Server not available"); return; }
		if(raw!=null && (raw.indexOf("<faultstring>")>-1)) { nexterr(raw); return; }
		else {
			client.setSecurity(basicAuthSecurity);

			var args = {
				"userName": data.userName,
				"credential": data.credential,
				"roleList": data.roleList,
				"claims": {
					"claimURI": "http://wso2.org/claims/lastname",
					"value": data.lastName
				},
				"requirePasswordChange": "false"
			};

			client.addUser(args, function(err, result, raw) {
			if(raw!=null && (raw.indexOf("<faultstring>")>-1)) { nexterr(raw); return; }
				else next();
			});
		}
	});
}

function addUserClaimValue(data, next) {
	var url = config.wso2_url + '/services/RemoteUserStoreManagerService?wsdl';
	soap.createClient(url, function(err, client) {
		if(client==null) { nexterr("Identity Server not available"); return; }

		client.setSecurity(basicAuthSecurity);

		var args = {
			"userName": data.userName,
			"claimURI": data.claimURI,
			"claimValue": data.value
		};

		client.addUserClaimValue(args, function(err, result, raw, soapHeader) {
			next();
		});
	});
}
