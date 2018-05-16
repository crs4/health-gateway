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
import ReactDOM from 'react-dom'
import { BrowserRouter } from 'react-router-dom';
import {Route, Switch} from 'react-router-dom';
import App from "./app";
import Confirm from "./confirm";

require('../css/yeti/bootstrap.min.css');
require('../css/custom.css');
require('../css/responsive_table.scss');

const wrapper = document.getElementById("content");
wrapper ? ReactDOM.render(
    <BrowserRouter>
        <Switch>
            <Route exact path='/' component={App}/>
            <Route path='/confirm_consents/' component={Confirm}/>
        </Switch>
    </BrowserRouter>, wrapper) : null;
