import React from 'react';
import DataProvider from './dataProvider';
import Consent from './consent';
import Welcome from './welcome';

class App extends React.Component {
    static renderConsents(data) {
        if (data === undefined) {
            return <Welcome/>
        }
        else {
            return (
                <Consent data={data}/>
            )
        }
    }

    render() {
        return (
            <DataProvider endpoint="/v1/consents/"
                          render={data => App.renderConsents(data)}/>
        )
    }
}

export default App;