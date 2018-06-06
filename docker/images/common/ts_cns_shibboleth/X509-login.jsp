<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <head>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>
    <title>Login</title>
  </head>
  <body onload="document.loginform.submit.focus()">
    <form id="loginform" action="https://idp.example.org/idp/Authn/X509/Login" method="post">
      <h1> Login </h1>
        <table>
          <tr>
            <td>
              Please make sure that your user certificate is properly
              configured in your web browser and click on the <strong>Certificate Login </strong> button.
            </td>
          </tr>
          <tr>
            <td>
              <input name="submit" type="submit" tabindex="1" accesskey="l"/>
            </td>
          </tr>
        </table>
        <p>
          <input type="checkbox" name="x509-pass-through" value="true" tabindex="2"/>
          Do not show this page for future logins
        </p>
    </form>
  </body>
</html>