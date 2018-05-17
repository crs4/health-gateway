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
import {Button, Modal, ModalHeader, ModalBody, ModalFooter} from 'reactstrap';
import DatePicker from 'react-datepicker'
import moment from "moment";
import {arrayToObject, iterate} from './utils'

class RevokeConsents extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            consents: this.props.data.slice(),
            revokeList: [],
        };
    }

    render() {
        const consents = this.state.consents;
        const rows = consents.map((c, i) => {
            if (c.status === "AC") {
                const checked = this.state.revokeList.includes(c.consent_id);
                return (
                    <tr key={i} className={i % 2 === 0 ? "table-light" : "table-secondary"}>
                        <td>{c.source.name}</td>
                        <td>{c.destination.name}</td>
                        <td>
                            <Profile data={c.profile}/>
                        </td>
                        <td>
                            <input type="checkbox" name="revoke_list" value={c.consent_id}
                                   checked={checked} onChange={this.checkBoxHandler.bind(this)}/>
                        </td>
                    </tr>
                )
            }
        });
        return (
            <form>
                <DjangoCSRFToken/>
                <table className="table">
                    <thead>
                    <tr className="table-active">
                        <th scope="col">Source</th>
                        <th scope="col">Destination</th>
                        <th scope="col">Data Sent</th>
                        <th scope="col">Revoke</th>
                    </tr>
                    </thead>
                    <tbody>
                    {rows}
                    </tbody>
                </table>
                <button type="button" className="btn btn-primary"
                        disabled={!this.canSubmit()}
                        onClick={this.sendRevoke.bind(this)}>Revoke Consents
                </button>
            </form>
        )
    }

    canSubmit() {
        return this.state.revokeList.length > 0;
    }

    checkBoxHandler(event) {
        let revokeList;
        if (event.target.checked) {
            revokeList = this.state.revokeList.concat(event.target.value);
        }
        else {
            revokeList = this.state.revokeList.filter(consentId => {
                return consentId !== event.target.value;
            });
        }
        this.setState({
            revokeList: revokeList
        })
    }

    sendRevoke() {
        axios.post('/v1/consents/revoke/', {
            consents: this.state.revokeList,
        }, {
            withCredentials: true,
            xsrfCookieName: 'csrftoken',
            xsrfHeaderName: 'X-CSRFToken'
        }).then((response) => {
            const newConsents = this.state.consents.filter((consent) => {
                return !response.data.revoked.includes(consent.consent_id);
            });

            this.setState({
                consents: newConsents,
                revokeList: []
            });
            this.props.notifier.success('Consents revoked correctly');

        }).catch((error) => {
            this.props.notifier.error('Erros while revoking consents');

        });
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
                    <tr key={k} className="table_responsive__row">
                        <td className="table_responsive__cell" data-title="Destination">
                            {c.destination.name}
                        </td>
                        <td className="table_responsive__cell" data-title="Source">
                            {c.source.name}
                        </td>
                        <td className="table_responsive__cell" data-title="Data Profile">
                            <Profile data={c.profile}/>
                        </td>
                        <td className="table_responsive__cell" data-title="Start Validity">
                            <DatePicker
                                minDate={moment(c.start_validity)}
                                maxDate={moment(c.expire_validity)}
                                selected={moment(c.start_validity)}
                                onChange={this.changeDate.bind(this, c.confirm_id, 'S')}
                            />
                        </td>
                        <td className="table_responsive__cell" data-title="End Validity">
                            <DatePicker
                                minDate={moment(c.start_validity)}
                                selected={moment(c.expire_validity)}
                                onChange={this.changeDate.bind(this, c.confirm_id, 'E')}
                            />
                            {/*{moment(c.expire_validity).format('L')}*/}
                        </td>
                        <td className="table_responsive__cell" data-title="Legal Notice">
                            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut
                            labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco
                            laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in
                            voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat
                            cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum
                        </td>
                        <td className="table_responsive__cell" data-title="Confirm">
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
                <table className="sheru-cp-section table_responsive">
                    <thead className="table_responsive__head">
                    <tr className="table_responsive__row">
                        <th className="table_responsive__cell table_responsive__cell--head" scope="col">Destination</th>
                        <th className="table_responsive__cell table_responsive__cell--head" scope="col">Source</th>
                        <th className="table_responsive__cell table_responsive__cell--head" scope="col">Data Profile
                        </th>
                        <th className="table_responsive__cell table_responsive__cell--head" scope="col">Start Validity
                        </th>
                        <th className="table_responsive__cell table_responsive__cell--head" scope="col">End Validity
                        </th>
                        <th className="table_responsive__cell table_responsive__cell--head" scope="col">Legal notice
                        </th>
                        <th className="table_responsive__cell table_responsive__cell--head" scope="col">
                            <input type="checkbox" name="confirm_all"
                                   disabled={this.state.sent}
                                   checked={checkedCounter === Object.keys(this.state.consents).length}
                                   onChange={this.checkBoxAllHandler.bind(this)}/>
                        </th>
                    </tr>
                    </thead>
                    <tbody className="table_responsive__body">
                    {rows}
                    </tbody>
                </table>
                <Button color="primary"
                        onClick={this.toggle.bind(this)}
                        disabled={!this.canSubmit()}>Confirm Consents</Button>
                <Modal isOpen={this.state.modal} toggle={this.toggle.bind(this)}>
                    <ModalHeader toggle={this.toggle.bind(this)}>Are you sure</ModalHeader>
                    <ModalBody>
                        Are you sure you want to authorize data transfer from the source to the selected
                        destinations?
                    </ModalBody>
                    <ModalFooter>
                        <Button color="primary" onClick={this.sendConfirmed.bind(this)}>Confirm</Button>{' '}
                        <Button color="secondary" onClick={this.toggle.bind(this)}>Cancel</Button>
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
            this.props.notifier.success('Consents confirmed correctly', () => {
                // window.location = callback
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

export {ConfirmConsents, RevokeConsents};