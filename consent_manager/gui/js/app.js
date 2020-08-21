// Copyright (c) 2017-2018 CRS4
//
// Permission is hereby granted, free of charge, to any person obtaining a copy of
// this software and associated documentation files (the "Software"), to deal in
// the Software without restriction, including without limitation the rights to use,
// copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
// and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all copies or
// substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
// INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
// AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
// DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import React from 'react';
import DataProvider from './dataProvider';
import {ConsentsController} from './consentReview';
import Welcome from './welcome';
import NotificationManager from './notificationManager';

class App extends React.Component {
    renderConsents(data) {
        if (data === undefined) {
            return <Welcome/>
        }
        else {
            return (
                <ConsentsController data={data} notifier={this.notifier}/>
            )
        }
    }

    componentDidMount() {
        this.notifier = this.refs.notificationManager;
    }

    render() {
        return (
            <div>
                <DataProvider endpoint="/v1/consents/"
                                 render={data => this.renderConsents(data)}/>
                <NotificationManager ref="notificationManager"/>
            </div>
        )
    }
}

export default App;