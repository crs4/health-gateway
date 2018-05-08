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

import React from 'react'
import Profile from './profile'
import DjangoCSRFToken from 'django-react-csrftoken'
import axios from 'axios';


class Consent extends React.Component {

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
                return (
                    <tr key={i} className={i % 2 === 0 ? "table-light" : "table-secondary"}>
                        <td>{c.source.name}</td>
                        <td>{c.destination.name}</td>
                        <td>
                            <Profile data={c.profile}/>
                        </td>
                        <td>
                            <input type="checkbox" name="revoke_list" value={c.consent_id}
                                   onChange={this.checkBoxHandler.bind(this)}/>
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
                    <tr className="table-success">
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
                        disabled={!this.isEnabled()}
                        onClick={this.sendRevoke.bind(this)}>Revoke Consents
                </button>
            </form>
        )
    }

    isEnabled() {
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
            const newConsents = this.state.consents.filter(function(consent) {
                console.log(consent);
                console.log(response.data.revoked.includes(consent.consent_id));
                return !response.data.revoked.includes(consent.consent_id)
            });
            this.setState({
                consents: newConsents,
                revokeList: []
            });

        }).catch((error) => {
            console.log(error);
        });
    }
}

export default Consent;