import React from "react";

class Welcome extends React.Component {
    render() {
        return (
            <div>
                <h1>Consent Manager</h1>
                <p className="lead">
                    This is the Consent Manager. Here you can handle your consents: you can revoke
                    consents and request to delete all data related to a consent already transferred.
                    Login to start handling your consents
                </p>
            </div>
        )
    }
}

export default Welcome