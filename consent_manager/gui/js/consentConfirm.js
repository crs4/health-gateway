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
import 'url-search-params-polyfill';
import DataProvider from './dataProvider';
import NotificationManager from './notificationManager';
import {arrayToObject, copy, getDate, iterate} from "./utils";
import Profile from "./profile";
import CustomDatePicker from "./customDatePicker";
import ReactMarkdown from "react-markdown";
import DjangoCSRFToken from "django-react-csrftoken";
import {Button, Modal, ModalBody, ModalFooter, ModalHeader} from "reactstrap";
import axios from "axios";

/**
 * Consent confirmation class. It shows the Consents and allows the user to
 * accept them
 */
class ConfirmConsents extends React.Component {

    constructor(props) {
        super(props);
        this.actions = {
            ACCEPT: 'accept',
            ABORT: 'abort'
        };
        this.alertMessages = {
            'accept': 'Are you sure you want to authorize data transfer to the destination from the selected\
                sources?',
            'abort': 'No consent will be granted. Are you sure you want to abort the ongoing process?'
        };
        this.actionLabels = {
            'accept': 'Yes, confirm',
            'abort': 'Yes, abort'
        };
        this.state = {
            consents: arrayToObject(this.props.data, 'confirm_id',
                {'checked': false, 'start_date_disabled': false, 'expire_date_disabled': false}),
            sent: false,
            modal: false,
            action: this.actions.ACCEPT
        };
    }

    render() {
        let rows = [];
        let checkedCounter = 0;
        for (let [k, c] of iterate(this.state.consents)) {
            if (c.checked === true) {
                checkedCounter++;
            }
            if (c.status === "PE") {
                rows.push(
                    <tr key={k} className="stack-table-row">
                        <td className="stack-table-cell" data-title="Destination">
                            {c.destination.name}
                        </td>
                        <td className="stack-table-cell" data-title="Source">
                            {c.source.name}
                        </td>
                        <td className="stack-table-cell" data-title="Data Profile">
                            <Profile data={c.profile}/>
                        </td>
                        <td className="stack-table-cell" data-title="Data Transfer Starting">
                            <CustomDatePicker
                                id={"start-date-picker-" + k}
                                disabled={c.start_date_disabled}
                                selected={getDate(c.start_validity)}
                                maxDate={getDate(c.expire_validity)}
                                label="Exclude Start Date"
                                onChangeDate={this.changeDate.bind(this, c.confirm_id, 'start')}
                                onChangeExclude={this.toggleDateSelection.bind(this, c.confirm_id, 'start')}/>
                        </td>
                        <td className="stack-table-cell" data-title="Data Transfer Ending">
                            <CustomDatePicker
                                id={"expire-date-picker-" + k}
                                disabled={c.expire_date_disabled}
                                selected={getDate(c.expire_validity)}
                                minDate={getDate(c.start_validity)}
                                label="Exclude End Date"
                                onChangeDate={this.changeDate.bind(this, c.confirm_id, 'expire')}
                                onChangeExclude={this.toggleDateSelection.bind(this, c.confirm_id, 'expire')}/>
                        </td>
                        <td className="stack-table-cell" data-title="Legal Notice">
                            <DataProvider endpoint={"/v1/legal-notices/" + c.legal_notice_version}
                                          accept="text/markdown, application/json"
                                          placeholder="Loading Legal Notice..."
                                          render={data => <ReactMarkdown source={data}/>}/>
                        </td>
                        <td className="stack-table-cell" data-title="Confirm">
                            <input type="checkbox" name="confirm_list" value={c.confirm_id}
                                   disabled={this.state.sent}
                                   checked={c.checked} onChange={this.checkBoxHandler.bind(this)}/>
                        </td>
                    </tr>
                )
            }
        }

        return (
            <form>
                <DjangoCSRFToken/>
                <table className="sheru-cp-section stack-table">
                    <thead className="stack-table-head">
                    <tr className="stack-table-row">
                        <th className="stack-table-cell stack-table-cell-header" scope="col">Destination</th>
                        <th className="stack-table-cell stack-table-cell-header" scope="col">Source</th>
                        <th className="stack-table-cell stack-table-cell-header" scope="col">Data Profile</th>
                        <th className="stack-table-cell stack-table-cell-header" scope="col">Data Transfer Starting</th>
                        <th className="stack-table-cell stack-table-cell-header" scope="col">End Transfer Starting</th>
                        <th className="stack-table-cell stack-table-cell-header" scope="col">Legal notice</th>
                        <th className="stack-table-cell stack-table-cell-header" scope="col">
                            <input type="checkbox" name="confirm_all"
                                   disabled={this.state.sent}
                                   checked={checkedCounter === Object.keys(this.state.consents).length}
                                   onChange={this.checkBoxAllHandler.bind(this)}/>
                        </th>
                    </tr>
                    </thead>
                    <tbody className="stack-table-body">
                    {rows}
                    </tbody>
                </table>
                <div style={{display: "flex"}}>
                    <Button id='btn-abort-consents'
                            style={{marginLeft: "auto", float: "left", margin: 10, padding: 10}}
                            color='primary'
                            onClick={this.modalUp.bind(this, this.actions.ABORT)}>
                        Abort consent operations</Button>{'          '}
                    <Button id='btn-confirm-consents'
                            style={{marginRight: "auto", float: "right", margin: 10, padding: 10}}
                            color='primary'
                            onClick={this.modalUp.bind(this, this.actions.ACCEPT)}
                            disabled={!this.canSubmit()}>
                        Accept Conditions for Selected Consent(s)</Button>
                </div>

                <Modal isOpen={this.state.modal} toggle={this.toggle.bind(this)}>
                    <ModalHeader toggle={this.toggle.bind(this)}>Please confirm</ModalHeader>
                    <ModalBody>
                        {this.alertMessages[this.state.action]}
                    </ModalBody>
                    <ModalFooter>
                        <Button color="primary" id="btn-modal-confirm-consents"
                                onClick={this.sendCommand.bind(this)}>
                            {this.actionLabels[this.state.action]}
                        </Button>{' '}
                        <Button color="secondary" id="btn-modal-cancel-consents"
                                onClick={this.toggle.bind(this)}>Cancel</Button>
                    </ModalFooter>
                </Modal>
            </form>
        )
    }

    canSubmit() {
        if (this.state.sent) {
            return false;
        } else {
            for (let [k, v] of iterate(this.state.consents)) {
                if (v['checked'] === true) {
                    return true;
                }
            }
        }
        return false;
    }

    changeDate(confirmId, startOrEnd, dateObject) {
        let consents = copy(this.state.consents);
        consents[confirmId][`${startOrEnd}_validity`] = dateObject.toISOString();
        this.setState({
            consents: consents
        });
    }

    toggleDateSelection(confirmId, startOrEnd, event) {
        let consents = copy(this.state.consents);
        consents[confirmId][`${startOrEnd}_date_disabled`] = event.target.checked;
        this.setState({
            consents: consents
        });
    }

    checkBoxHandler(event) {
        let consents = copy(this.state.consents);
        consents[event.target.value]['checked'] = event.target.checked;
        this.setState({
            consents: consents
        })
    }

    checkBoxAllHandler(event) {
        let consents = copy(this.state.consents);
        for (let [k, v] of iterate(consents)) {
            v['checked'] = event.target.checked;
        }
        this.setState({
            consents: consents
        });
    }

    toggle() {
        this.setState({
            modal: !this.state.modal
        })
    }

    modalUp(action) {
        this.setState({
            action: action,
            modal: true
        })
    }

    collectConsentsData() {
        let consentsData = {};
        for (let [key, consent] of iterate(this.state.consents)) {
            consentsData[key] = {
                'start_validity': consent.start_date_disabled ? null : consent.start_validity,
                'expire_validity': consent.expire_date_disabled ? null : consent.expire_validity
            }
        }
        return consentsData
    }

    sendCommand() {
        switch (this.state.action) {
            case this.actions.ACCEPT:
                this.sendConfirmed();
                break;
            case this.actions.ABORT:
                this.sendAbort();
                break;
        }
    }

    sendAbort() {
        this.toggle();

        axios.post('/v1/consents/abort/', {
                consents: this.collectConsentsData(),
            }
            , {
                withCredentials: true,
                xsrfCookieName: 'csrftoken',
                xsrfHeaderName: 'X-CSRFToken'
            }).then((response) => {
            const url = new URL(window.location.href);
            const confirmId = url.searchParams.get("confirm_id");
            const callback = `${this.props.callbackUrl}?success=false&status=aborted&consent_confirm_id=${confirmId}`;
            this.props.notifier.success(`Consents aborted correctly. Redirecting in 2 seconds...`, () => {
                window.location = callback
            });
        }).catch(() => {
            this.props.notifier.error('Errors while aborting consents.');
        });
    }


    sendConfirmed() {
        this.toggle();
        axios.post('/v1/consents/confirm/', {
            consents: this.collectConsentsData(),
        }, {
            withCredentials: true,
            xsrfCookieName: 'csrftoken',
            xsrfHeaderName: 'X-CSRFToken'
        }).then((response) => {
            const confirmedParams = response.data.confirmed.join('&consent_confirm_id=');
            const callback = `${this.props.callbackUrl}?success=true&consent_confirm_id=${confirmedParams}`;
            this.props.notifier.success('Consents confirmed correctly. Redirecting in 2 seconds...', () => {
                window.location = callback
            });
            this.setState({
                confirmed: [],
                sent: true
            });
        }).catch(() => {
            this.props.notifier.error('Errors while revoking consents');
        });
    }
}

class Confirm extends React.Component {

    constructor(props) {
        super(props);
        const params = new URLSearchParams(this.props.location.search);
        this.confirmId = params.getAll('confirm_id');
        this.callbackUrl = params.get('callback_url');
    }

    renderConsents(data) {
        return (
            <ConfirmConsents data={data}
                             notifier={this.notifier}
                             callbackUrl={this.callbackUrl}/>
        )
    }

    componentDidMount() {
        this.notifier = this.refs.notificationManager;
    }

    render() {
        return (
            <div>
                <DataProvider endpoint={'/v1/consents/find/'}
                                 params={{'confirm_id': this.confirmId}}
                                 render={data => this.renderConsents(data)}/>
                <NotificationManager ref="notificationManager"/>
            </div>
        )
    }
}

export default Confirm;
export {ConfirmConsents};