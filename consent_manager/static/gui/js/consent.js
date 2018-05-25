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
import Profile from './profile';
import DjangoCSRFToken from 'django-react-csrftoken';
import axios from 'axios';
import {Button, Modal, ModalBody, ModalFooter, ModalHeader, Table} from 'reactstrap';
import DatePicker from 'react-datepicker'
import moment from 'moment';
import {arrayToObject, iterate} from './utils';
import Pencil from 'react-icons/lib/fa/pencil';
import {Link} from 'react-router-dom';

moment.locale('it');

function sortConsents(a, b) {
    if (a['destination']['name'] < b['destination']['name']) {
        return -1;
    }
    if (a['destination']['name'] > b['destination']['name']) {
        return 1;
    }
    if (a['status'] < b['status']) {
        return -1;
    }
    if (a['status'] > b['status']) {
        return 1;
    }
    return 0;
}

class ManageConsents extends React.Component {

    constructor(props) {
        super(props);
        let consents = this.props.data.sort(sortConsents);
        this.status = {
            'AC': 'ACTIVE',
            'RE': 'REVOKED'
        };
        this.state = {
            consents: arrayToObject(consents, 'consent_id', {'collapsed': true})
        }
    }

    render() {
        let rows = [];
        let currentDest = "";
        for (let [k, c] of iterate(this.state.consents)) {
            if (c.destination.name !== currentDest) {
                rows.push(
                    <tr key={k + 'head'} className="stack-table-row">
                        <th className="stack-table-cell stack-table-cell-header
                        stack-table-cell-spanned" colSpan="6">{c.destination.name}
                        </th>
                    </tr>
                );
                currentDest = c.destination.name;
            }
            rows.push(
                <tr key={k} className="stack-table-row">
                    <td className="stack-table-cell" data-title="Source">
                        {c.source.name}
                    </td>
                    <td className="stack-table-cell" data-title="Status">
                        {this.status[c.status]}
                    </td>
                    <td className="stack-table-cell" data-title="Data Profile">
                        <Profile data={c.profile}/>
                    </td>
                    <td className="stack-table-cell" data-title="Start Validity">
                        {moment(c.start_validity).format('L')}
                    </td>
                    <td className="stack-table-cell" data-title="End Validity">
                        {moment(c.expire_validity).format('L')}
                    </td>
                    <td className="stack-table-cell stack-table-cell-modify">
                        <Link className='link' to={{
                            pathname: '/modify_consent/',
                            state: {
                                consent: c
                            }
                        }}>
                            <Pencil
                                size={20}/>
                        </Link>
                    </td>
                </tr>
            )
            ;
        }
        return (
            <form>
                <table className="sheru-cp-section stack-table">
                    <thead className="stack-table-head">
                    <tr className="stack-table-row">
                        <th className="stack-table-cell stack-table-cell-header" scope="col">Source</th>
                        <th className="stack-table-cell stack-table-cell-header" scope="col">Status</th>
                        <th className="stack-table-cell stack-table-cell-header" scope="col">Data Profile</th>
                        <th className="stack-table-cell stack-table-cell-header" scope="col">Start Validity</th>
                        <th className="stack-table-cell stack-table-cell-header" scope="col">End Validity</th>
                        <th className="stack-table-cell stack-table-cell-header" scope="col"/>
                    </tr>
                    </thead>
                    <tbody className="stack-table-body">
                    {rows}
                    </tbody>
                </table>
            </form>
        )
    }
}

class ConfirmConsents extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            consents: arrayToObject(this.props.data, 'confirm_id', {'checked': false}),
            sent: false,
            modal: false
        };
    }

    render() {
        let rows = [];
        let checkedCounter = 0;
        for (let [k, c] of iterate(this.state.consents)) {
            if (c['checked'] === true) {
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
                        <td className="stack-table-cell" data-title="Start Validity">
                            <DatePicker
                                minDate={moment(c.start_validity)}
                                maxDate={moment(c.expire_validity)}
                                selected={moment(c.start_validity)}
                                onChange={this.changeDate.bind(this, c.confirm_id, 'S')}
                            />
                        </td>
                        <td className="stack-table-cell" data-title="End Validity">
                            <DatePicker
                                minDate={moment(c.start_validity)}
                                selected={moment(c.expire_validity)}
                                onChange={this.changeDate.bind(this, c.confirm_id, 'E')}
                            />
                        </td>
                        <td className="stack-table-cell" data-title="Legal Notice">
                            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut
                            labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco
                            laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in
                            voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat
                            cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum
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
                        <th className="stack-table-cell stack-table-cell-header" scope="col">Data Profile
                        </th>
                        <th className="stack-table-cell stack-table-cell-header" scope="col">Start Validity
                        </th>
                        <th className="stack-table-cell stack-table-cell-header" scope="col">End Validity
                        </th>
                        <th className="stack-table-cell stack-table-cell-header" scope="col">Legal notice
                        </th>
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
                <Button id='btn-confirm-consents'
                        color='primary'
                        onClick={this.toggle.bind(this)}
                        disabled={!this.canSubmit()}>Confirm Consents</Button>
                <Modal isOpen={this.state.modal} toggle={this.toggle.bind(this)}>
                    <ModalHeader toggle={this.toggle.bind(this)}>Are you sure</ModalHeader>
                    <ModalBody>
                        Are you sure you want to authorize data transfer from the source to the selected
                        destinations?
                    </ModalBody>
                    <ModalFooter>
                        <Button color="primary" id="btn-modal-confirm-consents"
                                onClick={this.sendConfirmed.bind(this)}>Confirm</Button>{' '}
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
        }
        else {
            for (let [k, v] of iterate(this.state.consents)) {
                if (v['checked'] === true) {
                    return true;
                }
            }
        }
        return false;
    }

    changeDate(confirmId, startOrEnd, dateObject) {
        if (startOrEnd === 'S') {
            startOrEnd = 'start'
        }
        else {
            startOrEnd = 'expire'
        }
        let consents = Object.assign({}, this.state.consents);
        consents[confirmId][startOrEnd + '_validity'] = dateObject.format();
        this.setState({
            consents: consents
        });
    }

    checkBoxHandler(event) {
        let consents = Object.assign({}, this.state.consents);
        consents[event.target.value]['checked'] = event.target.checked;
        this.setState({
            consents: consents
        })
    }

    checkBoxAllHandler(event) {
        let consents = Object.assign({}, this.state.consents);
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

    sendConfirmed() {
        this.toggle();
        let consentsData = {};
        for (let [k, v] of iterate(this.state.consents)) {
            if (v['checked'] === true) {
                consentsData[k] = {
                    'start_validity': v['start_validity'],
                    'expire_validity': v['expire_validity']
                }
            }
        }

        axios.post('/v1/consents/confirm/', {
            consents: consentsData,
        }, {
            withCredentials: true,
            xsrfCookieName: 'csrftoken',
            xsrfHeaderName: 'X-CSRFToken'
        }).then((response) => {
            const confirmedParams = response.data.confirmed.join('&consent_confirm_id=');
            const callback = this.props.callbackUrl + '?success=true&consent_confirm_id=' + confirmedParams;
            this.props.notifier.success('Consents confirmed correctly. Redirecting in 2 seconds', () => {
                window.location = callback
            });
            this.setState({
                confirmed: [],
                sent: true
            });
        }).catch((error) => {
            this.props.notifier.error('Erros while revoking consents');
        });
    }
}

class ModifyConsent extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            consent: this.props.location.state.consent,
            modal: false
        };
    }

    render() {
        const consent = this.state.consent;
        return (
            <div>
                <div className='table-responsive-md details-table-container'>
                    <DjangoCSRFToken/>
                    <table className='sheru-cp-section details-table'>
                        <tbody className='details-table-body'>
                        <tr className='details-table-row'>
                            <td className='details-table-cell details-table-cell-key'>
                                Destination
                            </td>
                            <td className='details-table-cell details-table-cell-value'>
                                {consent.destination.name}
                            </td>
                        </tr>
                        <tr className='details-table-row'>
                            <td className='details-table-cell details-table-cell-key'>
                                Source
                            </td>
                            <td className='details-table-cell details-table-cell-value'>
                                {consent.source.name}
                            </td>
                        </tr>
                        <tr className='details-table-row'>
                            <td className='details-table-cell details-table-cell-key'>
                                Data Profile
                            </td>
                            <td className='details-table-cell details-table-cell-value'>
                                <Profile data={consent.profile}/>
                            </td>
                        </tr>
                        <tr className='details-table-row'>
                            <td className='details-table-cell details-table-cell-key'>
                                Start Date
                            </td>
                            <td className='details-table-cell details-table-cell-value'>
                                <DatePicker
                                    minDate={moment(consent.start_validity)}
                                    maxDate={moment(consent.expire_validity)}
                                    selected={moment(consent.start_validity)}
                                    onChange={this.changeDate.bind(this, 'S')}
                                />
                            </td>
                        </tr>
                        <tr className='details-table-row'>
                            <td className='details-table-cell details-table-cell-key'>
                                End Date
                            </td>
                            <td className='details-table-cell details-table-cell-value'>
                                <DatePicker
                                    minDate={moment(consent.start_validity)}
                                    selected={moment(consent.expire_validity)}
                                    onChange={this.changeDate.bind(this, 'E')}
                                />
                            </td>
                        </tr>
                        <tr className='details-table-row'>
                            <td className='details-table-cell details-table-cell-key'>
                                Legal Notice
                            </td>
                            <td className='details-table-cell details-table-cell-value'>
                                Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
                                incididunt ut
                                labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
                                ullamco
                                laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit
                                in
                                voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat
                                cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum
                            </td>
                        </tr>
                        </tbody>
                    </table>
                </div>
                <Button id='btn-cancel'
                        color='info'
                        onClick={this.props.history.goBack}>
                    Cancel
                </Button>{' '}
                <Button id='btn-modify'
                        color='primary'>
                    Modify
                </Button>{' '}
                <Button id='btn-revoke'
                        color='success'>
                    Revoke
                </Button>{' '}
                <Button id='btn-delete'
                        color='danger'>
                    Delete all data
                </Button>
                <Modal isOpen={this.state.modal} toggle={this.toggle.bind(this)}>
                    <ModalHeader toggle={this.toggle.bind(this)}>Are you sure</ModalHeader>
                    <ModalBody>
                        Are you sure you want to authorize data transfer from the source to the selected
                        destinations?
                    </ModalBody>
                    <ModalFooter>
                        {/*<Button color="primary" id="btn-modal-confirm-consents"*/}
                        {/*onClick={this.sendConfirmed.bind(this)}>Confirm</Button>{' '}*/}
                        {/*<Button color="secondary" id="btn-modal-cancel-consents"*/}
                        {/*onClick={this.toggle.bind(this)}>Cancel</Button>*/}
                    </ModalFooter>
                </Modal>
            </div>
        )
    }

    changeDate(startOrEnd, dateObject) {
        if (startOrEnd === 'S') {
            startOrEnd = 'start'
        }
        else {
            startOrEnd = 'expire'
        }
        let consent = Object.assign({}, this.state.consent);
        consent[startOrEnd + '_validity'] = dateObject.format();
        this.setState({
            consent: consent
        });
    }

    toggle() {
        this.setState({
            modal: !this.state.modal
        })
    }
}

export {ConfirmConsents, ManageConsents, ModifyConsent};