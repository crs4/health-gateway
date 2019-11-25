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
import { Button, Modal, ModalBody, ModalFooter, ModalHeader } from 'reactstrap';
import moment from 'moment';
import { arrayToObject, copy, iterate, getDate, getFormattedDate } from './utils';
import Pencil from 'react-icons/lib/fa/pencil';
import PropTypes from 'prop-types';
import NotificationManager from './notificationManager';
import CustomDatePicker from './customDatePicker';

moment.locale('it');  // This should correspond to the timezone set in Django

const status = {
    'AC': 'ACTIVE',
    'RE': 'REVOKED'
};

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

/**
 * Consent confirmation class. It shows the Consents and allows the user to 
 * accept them
 */
class ConfirmConsents extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            consents: arrayToObject(this.props.data, 'confirm_id',
                { 'checked': false, 'start_date_disabled': false, 'expire_date_disabled': false }),
            sent: false,
            modal: false,
            modal2: false
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
                            <Profile data={c.profile} />
                        </td>
                        <td className="stack-table-cell" data-title="Data Transfer Starting">
                            <CustomDatePicker
                                id={"start-date-picker-" + k}
                                disabled={c.start_date_disabled}
                                selected={getDate(c.start_validity)}
                                maxDate={getDate(c.expire_validity)}
                                label="Exclude Start Date"
                                onChangeDate={this.changeDate.bind(this, c.confirm_id, 'start')}
                                onChangeExclude={this.toggleDateSelection.bind(this, c.confirm_id, 'start')} />
                        </td>
                        <td className="stack-table-cell" data-title="Data Transfer Ending">
                            <CustomDatePicker
                                id={"expire-date-picker-" + k}
                                disabled={c.expire_date_disabled}
                                selected={getDate(c.expire_validity)}
                                minDate={getDate(c.start_validity)}
                                label="Exclude End Date"
                                onChange={this.changeDate.bind(this, c.confirm_id, 'expire')}
                                onChangeExclude={this.toggleDateSelection.bind(this, c.confirm_id, 'expire')} />
                        </td>
                        <td className="stack-table-cell" data-title="Legal Notice">
                            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
                            incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
                            nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
                        </td>
                        <td className="stack-table-cell" data-title="Confirm">
                            <input type="checkbox" name="confirm_list" value={c.confirm_id}
                                disabled={this.state.sent}
                                checked={c.checked} onChange={this.checkBoxHandler.bind(this)} />
                        </td>
                    </tr>
                )
            }
        }

        return (
            <form>
                <DjangoCSRFToken />
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
                                    onChange={this.checkBoxAllHandler.bind(this)} />
                            </th>
                        </tr>
                    </thead>
                    <tbody className="stack-table-body">
                        {rows}
                    </tbody>
                </table>
                <div style={{ display: "flex"}}>
                    <Button id='btn-abort-consents'
                            style={{ marginLeft: "auto", float: "left", margin:10, padding: 10}}
                            color='primary'
                            onClick={this.toggle2.bind(this)}>
                            Abort consent operations</Button>{'          '}
                    <Button id='btn-confirm-consents'
                            style={{ marginRight: "auto", float: "right", margin:10, padding: 10}}
                            color='primary'
                            onClick={this.toggle.bind(this)}
                            disabled={!this.canSubmit()}>
                            Accept Conditions for Selected Consent(s)</Button>
                </div>

                <Modal isOpen={this.state.modal2} toggle={this.toggle2.bind(this)}>
                    <ModalHeader toggle={this.toggle2.bind(this)}></ModalHeader>
                    <ModalBody>Are you sure you want to abort consent process?</ModalBody>
                    <ModalFooter>
                        <Button color="primary" id="btn-modal-abort-consents"
                                onClick={this.sendAbort.bind(this)}>Yes, Abort.</Button>{' '}
                        <Button color="secondary" id="btn-modal-cancel-consents"
                                onClick={this.toggle2.bind(this)}>Cancel</Button>
                    </ModalFooter>
                </Modal>

                <Modal isOpen={this.state.modal} toggle={this.toggle.bind(this)}>
                    <ModalHeader toggle={this.toggle.bind(this)}></ModalHeader>
                    <ModalBody>
                        Are you sure you want to authorize data transfer to the destination from the selected
                        sources?
                    </ModalBody>
                    <ModalFooter>
                        <Button color="primary" id="btn-modal-confirm-consents"
                            onClick={this.sendConfirmed.bind(this)}>Authorize</Button>{' '}
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
        let consents = copy(this.state.consents);
        consents[confirmId][`${startOrEnd}_validity`] = dateObject.format();
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

    toggle2() {
        this.setState({
            modal2: !this.state.modal2
        })
    }

    sendAbort() {
        this.toggle2();
        let consentsData = {};
        for (let [key, consent] of iterate(this.state.consents)) {
            consentsData[key] = {
                'start_validity': consent.start_date_disabled ? null : consent.start_validity,
                'expire_validity': consent.expire_date_disabled ? null : consent.expire_validity
            }
        }

        axios.post('/v1/consents/abort/', {
                consents: consentsData,
            }
        , {
            withCredentials: true,
            xsrfCookieName: 'csrftoken',
            xsrfHeaderName: 'X-CSRFToken'
        }).then((response) => {
            var url = new URL(window.location.href);
            var confirmId = url.searchParams.get("confirm_id");
            const callback = `${this.props.callbackUrl}?success=false&status=aborted&confirm_id=${confirmId}`;
            this.props.notifier.success(`Consents aborted correctly. Redirecting in 2 seconds...`, () => {
                window.location = callback});
        }).catch(() => {
            this.props.notifier.error('Errors while aborting consents.');
        });
    }



    sendConfirmed() {
        this.toggle();
        let consentsData = {};
        for (let [key, consent] of iterate(this.state.consents)) {
            if (consent.checked === true) {
                consentsData[key] = {
                    'start_validity': consent.start_date_disabled ? null : consent.start_validity,
                    'expire_validity': consent.expire_date_disabled ? null : consent.expire_validity
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

/**
 * Consents list class. It shows the list of consents for the user
 */
class ConsentsList extends React.Component {
    render() {
        let rows = [];
        let currentDest = "";
        for (let [k, c] of iterate(this.props.consents)) {
            if (c.destination.name !== currentDest) {
                rows.push(
                    <tr key={`${k}head`} className="stack-table-row">
                        <th className="stack-table-cell stack-table-cell-header stack-table-cell-spanned"
                            colSpan="6">
                            {c.destination.name}
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
                        {status[c.status]}
                    </td>
                    <td className="stack-table-cell" data-title="Data Profile">
                        <Profile data={c.profile} />
                    </td>
                    <td className="stack-table-cell" data-title="Start Transfer Date">
                        {getFormattedDate(c.start_validity)}
                    </td>
                    <td className="stack-table-cell" data-title="End Transfer Date">
                        {getFormattedDate(c.expire_validity)}
                    </td>
                    <td className="stack-table-cell stack-table-cell-modify"
                        onClick={this.callSelectConsent.bind(this, c)}>
                        <Pencil size={20} />
                    </td>
                </tr>
            );
        }
        return (
            <form>
                <table className="sheru-cp-section stack-table">
                    <thead className="stack-table-head">
                        <tr className="stack-table-row">
                            <th className="stack-table-cell stack-table-cell-header" scope="col">Source</th>
                            <th className="stack-table-cell stack-table-cell-header" scope="col">Status</th>
                            <th className="stack-table-cell stack-table-cell-header" scope="col">Data Profile</th>
                            <th className="stack-table-cell stack-table-cell-header" scope="col">Start Transfer Date</th>
                            <th className="stack-table-cell stack-table-cell-header" scope="col">End Transfer Date</th>
                            <th className="stack-table-cell stack-table-cell-header" scope="col" />
                        </tr>
                    </thead>
                    <tbody className="stack-table-body">
                        {rows}
                    </tbody>
                </table>
            </form>
        )
    }

    callSelectConsent(c) {
        this.props.selectConsent(c);
    }
}

ConsentsList.propTypes = {
    consents: PropTypes.object,
    selectConsent: PropTypes.func.isRequired
};

/**
 * Consent details class. It shows the details of a consent and allows operation like
 * revoking or modifying the datetime range
 */
class ConsentDetails extends React.Component {
    constructor(props) {
        super(props);
        this.actions = {
            REVOKE: 'revoke',
            MODIFY: 'modify'
        };
        this.alertMessages = {
            'revoke': 'If you revoke the consent all the messages incoming from the source ' +
                'will not be sent to the destination anymore.\n' +
                'The data already sent to the destination will be kept\n' +
                'Do you want to continue?',
            'modify': 'This action will change the consent data. Are you sure you want to continue?'
        };

        let originalConsent = copy(this.props.consent)
        originalConsent['start_date_disabled'] = this.props.consent['start_validity'] == null;
        originalConsent['expire_date_disabled'] = this.props.consent['expire_validity'] == null;

        this.state = {
            originalConsent: originalConsent,
            currentConsent: copy(originalConsent),
            modal: null
        };
    }

    render() {
        const consent = this.state.currentConsent;
        return (
            <div>
                <div className='table-responsive-md details-table-container'>
                    <DjangoCSRFToken />
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
                                    Status
                            </td>
                                <td className='details-table-cell details-table-cell-value'>
                                    {status[consent.status]}
                                </td>
                            </tr>
                            <tr className='details-table-row'>
                                <td className='details-table-cell details-table-cell-key'>
                                    Data Profile
                            </td>
                                <td className='details-table-cell details-table-cell-value'>
                                    <Profile data={consent.profile} />
                                </td>
                            </tr>
                            <tr className='details-table-row'>
                                <td className='details-table-cell details-table-cell-key'>
                                    Start Date
                            </td>
                                <td className='details-table-cell details-table-cell-value'>
                                    <CustomDatePicker
                                        label="Exclude Start Date"
                                        id={"start-date-picker"}
                                        disabled={consent.start_date_disabled}
                                        selected={getDate(consent.start_validity)}
                                        maxDate={getDate(consent.expire_validity)}
                                        onChangeDate={this.setDate.bind(this, 'start')}
                                        onChangeExclude={this.toggleExcludeDate.bind(this, 'start')} />
                                </td>
                            </tr>
                            <tr className='details-table-row'>
                                <td className='details-table-cell details-table-cell-key'>
                                    End Date
                            </td>
                                <td className='details-table-cell details-table-cell-value'>
                                    <CustomDatePicker
                                        label="Exclude End Date"
                                        id={"end-date-picker"}
                                        disabled={consent.expire_date_disabled}
                                        selected={getDate(consent.expire_validity)}
                                        minDate={getDate(consent.start_validity)}
                                        onChangeDate={this.setDate.bind(this, 'expire')}
                                        onChangeExclude={this.toggleExcludeDate.bind(this, 'expire')} />
                                </td>
                            </tr>
                            <tr className='details-table-row'>
                                <td className='details-table-cell details-table-cell-key'>
                                    Legal Notice
                            </td>
                                <td className='details-table-cell details-table-cell-value'>
                                    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
                                    incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
                                    nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
                            </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <Button id='btn-back'
                    color='info'
                    onClick={this.goBack.bind(this)}>
                    Back
                </Button>{' '}
                <Button id='btn-modify'
                    color='primary'
                    disabled={!this.canSubmit()}
                    onClick={this.toggleModal.bind(this, this.actions.MODIFY)}>
                    Modify
                </Button>{' '}
                <Button id='btn-revoke'
                    color='success'
                    disabled={consent.status !== 'AC'}
                    onClick={this.toggleModal.bind(this, this.actions.REVOKE)}>
                    Revoke
                </Button>{' '}
                <Button id='btn-delete'
                    color='danger'>
                    Delete all data
                </Button>
                <Modal isOpen={this.state.modal !== null} toggle={this.toggleModal.bind(this, this.state.modal)}>
                    <ModalHeader toggle={this.toggleModal.bind(this, this.state.modal)}>Are you sure</ModalHeader>
                    <ModalBody>
                        {this.alertMessages[this.state.modal]}
                    </ModalBody>
                    <ModalFooter>
                        <Button color="primary" id="btn-modal-ok"
                            onClick={this.sendCommand.bind(this, this.state.modal)}>OK</Button>{' '}
                        <Button color="secondary" id="btn-modal-cancel"
                            onClick={this.toggleModal.bind(this, this.state.modal)}>Cancel</Button>
                    </ModalFooter>
                </Modal>
            </div>
        )
    }

    /**
     * Method to check if it is possible to submit the changes
     */
    canSubmit() {
        let current = this.state.currentConsent;
        let original = this.state.originalConsent;
        return current.status === 'AC' && (
            (current.start_validity != original.start_validity && !current.start_date_disabled) ||
            (current.expire_validity != original.expire_validity && !current.expire_date_disabled) ||
            (current.start_date_disabled != original.start_date_disabled && current.start_validity != null) ||
            (current.expire_date_disabled != original.expire_date_disabled && current.expire_validity != null)
        );

    }

    /**
     * Change the current state of the consent according to the "Exclude date" checkbox
     * @param {string} startOrExpire the date to toggle. It must be `start` or `end`
     * @param {Object} event the event that triggered the method call
     */
    toggleExcludeDate(startOrExpire, event) {
        let consent = copy(this.state.currentConsent);
        consent[`${startOrExpire}_date_disabled`] = event.target.checked;
        this.setState({
            currentConsent: consent
        });
    }

    /**
     * Set the value of the start or end date
     * @param {string} startOrEnd the date to set. It must be `start` or `end`
     * @param {Date} dateObject the new date value
     */
    setDate(startOrEnd, dateObject) {
        let consent = copy(this.state.currentConsent);
        consent[`${startOrEnd}_validity`] = dateObject.format();
        this.setState({
            currentConsent: consent
        });
    }

    /**
     * Open or close the confirmation modal window
     * @param {} action 
     */
    toggleModal(action) {
        this.setState({
            modal: this.state.modal === null ? action : null
        })
    }

    goBack() {
        this.props.goBack(this.state.originalConsent);
    }

    sendCommand(action) {
        const consentId = this.state.currentConsent.consent_id;

        switch (action) {
            case this.actions.REVOKE:
                this.revoke(consentId);
                break;
            case this.actions.MODIFY:
                this.modify(consentId);
                break;
        }
    }

    revoke(consentId) {
        axios.post(`/v1/consents/${consentId}/revoke/`, {}, {
            withCredentials: true,
            xsrfCookieName: 'csrftoken',
            xsrfHeaderName: 'X-CSRFToken'
        }).then(() => {
            let consent = copy(this.state.currentConsent);
            consent.status = 'RE';
            this.setState({
                originalConsent: consent,
                currentConsent: consent,
            });
            this.toggleModal(this.actions.REVOKE);
            this.props.notifier.success('Consent revoked correctly');
        }).catch(() => {
            this.toggleModal(this.actions.REVOKE);
            this.props.notifier.error('Errors happened revoking consent');
        });
    }

    modify(consentId) {
        const start_validity = this.state.currentConsent.start_date_disabled ? null :
            this.state.currentConsent.start_validity;
        const expire_validity = this.state.currentConsent.expire_date_disabled ? null :
            this.state.currentConsent.expire_validity;

        axios.put(`/v1/consents/${consentId}/`, {
            'start_validity': start_validity,
            'expire_validity': expire_validity
        }, {
            withCredentials: true,
            xsrfCookieName: 'csrftoken',
            xsrfHeaderName: 'X-CSRFToken'
        }).then(() => {
            this.toggleModal(this.actions.MODIFY);

            let originalConsent = copy(this.state.currentConsent);
            originalConsent['start_validity'] = start_validity;
            originalConsent['expire_validity'] = expire_validity;
            let newCurrentConsent = copy(originalConsent);

            this.setState({
                originalConsent: originalConsent,
                currentConsent: newCurrentConsent,
            });

            this.props.notifier.success('Consent modified correctly');
        }).catch(() => {
            this.toggleModal(this.actions.MODIFY);
            this.props.notifier.error('Errors happened modifying consent');
        });
    }
}

ConsentDetails.propTypes = {
    consent: PropTypes.object,
    notifier: PropTypes.instanceOf(NotificationManager),
    goBack: PropTypes.func.isRequired

};

class ConsentsController extends React.Component {

    constructor(props) {
        super(props);
        let consents = this.props.data.sort(sortConsents);
        this.state = {
            consents: arrayToObject(consents, 'consent_id', { 'collapsed': true }),
            currentConsent: null
        }
    }

    render() {
        if (this.state.currentConsent === null) {
            return (<ConsentsList consents={this.state.consents}
                selectConsent={this.selectConsent.bind(this)} />)
        }
        else {
            return (<ConsentDetails consent={this.state.currentConsent}
                notifier={this.props.notifier}
                goBack={this.doneModify.bind(this)} />)
        }
    }

    selectConsent(consent) {
        this.setState({
            currentConsent: consent
        });
    }

    doneModify(consent) {
        let consents = copy(this.state.consents);
        consents[consent.consent_id] = consent;
        this.setState({
            consents: consents,
            currentConsent: null
        });
    }
}

ConsentsController.propTypes = {
    data: PropTypes.array,
    notifier: PropTypes.instanceOf(NotificationManager)
};

export { ConfirmConsents, ConsentsController, ConsentDetails as ConsentManager };