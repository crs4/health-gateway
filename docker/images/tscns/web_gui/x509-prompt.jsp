<%@ taglib uri="http://www.springframework.org/tags" prefix="spring" %>
<%@ taglib uri="urn:mace:shibboleth:2.0:idp:ui" prefix="idpui" %>
<%@ page import="javax.servlet.http.Cookie" %>
<%@ page import="org.opensaml.profile.context.ProfileRequestContext" %>
<%@ page import="net.shibboleth.idp.authn.ExternalAuthentication" %>
<%@ page import="net.shibboleth.idp.authn.context.AuthenticationContext" %>
<%@ page import="net.shibboleth.idp.profile.context.RelyingPartyContext" %>
<%@ page import="net.shibboleth.idp.ui.context.RelyingPartyUIContext" %>

<%
final Cookie[] cookies = request.getCookies();
if (cookies != null) {
    for (final Cookie cookie : cookies) {
        if (cookie.getName().equals("x509passthrough")) {
        	response.sendRedirect(request.getContextPath() + "/Authn/X509?"
                + ExternalAuthentication.CONVERSATION_KEY + "="
                + request.getParameter(ExternalAuthentication.CONVERSATION_KEY));
        	return;
        }
    }
}

final String key = ExternalAuthentication.startExternalAuthentication(request);
final ProfileRequestContext prc = ExternalAuthentication.getProfileRequestContext(key, request);
final AuthenticationContext authnContext = prc.getSubcontext(AuthenticationContext.class);
final RelyingPartyContext rpContext = prc.getSubcontext(RelyingPartyContext.class);
final RelyingPartyUIContext rpUIContext = authnContext.getSubcontext(RelyingPartyUIContext.class);
final boolean identifiedRP = rpUIContext != null && !rpContext.getRelyingPartyId().contains(rpUIContext.getServiceName());
%>

<!DOCTYPE html>
<html>

<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>
    <spring:message code="idp.title" text="Web Login Service" />
  </title>
</head>

<body>
  <div class="wrapper">
    <div class="container">
      <div class="content">
        <div class="column one">
          <form id="loginform" action="<%= request.getContextPath() %>/Authn/X509" method="post">

            <input type="hidden" name="<%= ExternalAuthentication.CONVERSATION_KEY %>" 
              value="<%= request.getParameter(ExternalAuthentication.CONVERSATION_KEY) %>">

            <% if (identifiedRP) { %>
            <legend>
              <spring:message code="idp.login.loginTo" text="Login to" />
              <idpui:serviceName uiContext="<%= rpUIContext %>" />
            </legend>
            <% } %>

            <div class="container">
              <h2 align="center">TS/CNS Login Authentication Page</h2>
              <div class="panel panel-default">
                <div class="panel-heading">TS/CNS Identification</div>
                <div class="panel-body">
                  Ensure you have your TS/CNS reader properly connected and with the required rivers installed.
                  Insert your TS/CNS card into the reader, then click on the TS/CNS Login button. You will be asked
                  to enter your PIN and to confirm certificate selection.
                </div>
              </div>
            </div>
            <br />
            <div class="form-element-wrapper col-sm-4 col-sm-offset-4 text-center">
              <button class="form-element form-button" type="submit" name="login" value="1" tabindex="1" accesskey="l">TS/CNS
                Login</button>
            </div>

          </form>

          <% if (identifiedRP) { %>
          <p>
            <idpui:serviceLogo uiContext="<%= rpUIContext %>">default</idpui:serviceLogo>
            <idpui:serviceDescription uiContext="<%= rpUIContext %>">SP description</idpui:serviceDescription>
          </p>
          <% } %>

        </div>
      </div>
    </div>
  </div>

</body>

</html>