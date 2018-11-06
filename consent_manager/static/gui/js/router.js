import React from 'react';
import {Route, Switch} from 'react-router-dom';
import App from './app'
import Confirm from './confirm'

const Main = () => (
    <main>
        <Switch>
            <Route exact path='/' component={App}/>
            <Route path='/v1/consents/confirm/' component={Confirm}/>
        </Switch>
    </main>
);

export default Main;
