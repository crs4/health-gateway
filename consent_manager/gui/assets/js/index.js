import React from 'react';
import ReactDOM from 'react-dom';
import DataProvider from './dataProvider';
import Consent from './consent';
import Welcome from './welcome'


class App extends React.Component {

    static renderConsents(data) {
        if (data === undefined) {
            return <Welcome />
        }
        else {
            console.log("Consent");
            return <Consent data={data}/>
        }
    }

    render() {
        return (
            <DataProvider endpoint="/v1/consents/"
                          render={data => App.renderConsents(data)}/>
        )
    }
}

const wrapper = document.getElementById("content");
wrapper ? ReactDOM.render(<App/>, wrapper) : null;
