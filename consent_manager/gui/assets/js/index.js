import React from 'react';
import ReactDOM from 'react-dom';
import DataProvider from "./dataProvider";
import Consent from "./consent";

class Content extends React.Component {
    render() {
        return (
            <div>
                <h1>Consent Manager</h1>
                <p className="lead"> This is the Consent Manager.Here you can handle your consents: you can revoke
                    consents and request to delete all data related to a consent already transferred. Login to start
                    handling
                    your consents </p>
            </div>
        )
    }
}

const App = () => (
  <DataProvider endpoint="/v1/consents/"
                render={data => <Consent data={data} />} />
);

const wrapper = document.getElementById("content");
wrapper ? ReactDOM.render(<App />, wrapper) : null;
