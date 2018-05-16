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
import moment from "moment";

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
            consents: this.props.data.slice(),
            confirmedList: [],
            sent: false,
            modal: false
        };
    }

    render() {
        const consents = this.state.consents;
        const rows = consents.map((c, i) => {
            if (c.status === "PE") {
                const checked = this.state.confirmedList.includes(c.confirm_id);
                return (
                    <tr key={i} className="table_responsive__row">
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
                            {moment(c.start_validity).format('L')}
                        </td>
                        <td className="table_responsive__cell" data-title="End Validity">
                            {moment(c.expire_validity).format('L')}
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
                                   checked={checked} onChange={this.checkBoxHandler.bind(this)}/>
                        </td>
                    </tr>
                )
            }
        });
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
                                   checked={this.state.confirmedList.length === this.state.consents.length}
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
        return this.state.confirmedList.length > 0 && !this.state.sent;
    }

    checkBoxHandler(event) {
        let confirmedList;
        if (event.target.checked) {
            confirmedList = this.state.confirmedList.concat(event.target.value);
        }
        else {
            confirmedList = this.state.confirmedList.filter(confirmId => {
                return confirmId !== event.target.value;
            });
        }
        this.setState({
            confirmedList: confirmedList
        })
    }

    checkBoxAllHandler(event) {
        let confirmedList;
        if (event.target.checked) {
            confirmedList = this.state.consents.map((consent) => {
                return consent.confirm_id;
            });
        }
        else {
            confirmedList = [];
        }
        this.setState({
            confirmedList: confirmedList
        })
    }

    toggle() {
        this.setState({
            modal: !this.state.modal
        })
    }

    sendConfirmed() {
        this.toggle();
        axios.post('/v1/consents/confirm/', {
            confirm_ids: this.state.confirmedList,
        }, {
            withCredentials: true,
            xsrfCookieName: 'csrftoken',
            xsrfHeaderName: 'X-CSRFToken'
        }).then((response) => {
            const confirmedParams = response.data.confirmed.join('&consent_confirm_id=');
            const callback = this.props.callbackUrl + '?success=true&consent_confirm_id=' + confirmedParams;
            this.props.notifier.success('Consents confirmed correctly', () => {
                window.location = callback
            });
            this.setState({
                confirmedList: [],
                sent: true
            });
        }).catch((error) => {
            this.props.notifier.error('Erros while revoking consents');
        });
    }
}

export {ConfirmConsents, RevokeConsents};