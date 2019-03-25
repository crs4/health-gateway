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

import React from "react";
import { InputGroup, Input, InputGroupAddon } from 'reactstrap'
import { Bootstrap2Toggle } from "react-bootstrap-toggle";
import PropTypes from 'prop-types';


class Profile extends React.Component {
    constructor() {
        super();

        // const profiles = JSON.parse(this.props.data.payload);
        this.profiles = [{
            'id': 'aaabbbcccddd',
            'version': '1.0.0',
            'clinicalDomain': 'Laboratory',
            'data': {
                'sections': [{
                    'name': 'Coagulation Studies',
                    'items': [{ 'name': 'Proteina S Funzionale' }]
                },
                {
                    'name': 'Microbiology Studies',
                    'items': [{ 'name': 'VIRUS ANTIGENI IN MATERIALI BIOLOGICI RICERCA DIRETTA (E.I.A.)' },
                    { 'name': 'E. COLI ENTEROPATOGENI NELLE FECI ESAME COLTURALE' }]
                },
                {
                    'name': 'Hematology Studies',
                    'items': [{ 'name': 'ANTICORPI ANTI CARDIOLIPINA' }]
                },
                {
                    'name': 'Serology Studies',
                    'items': [{ 'name': 'ANTICORPI ANTIPIASTRINE' }]
                },
                {
                    'name': 'Chemistry Studies',
                    'items': [{ 'name': 'Hb - EMOGLOBINA [Sg/La]' }]
                }]
            }
        }];

        var activeAuthorization = Array(this.profiles[0].data.sections.length);
        for (var i = 0; i < activeAuthorization.length; i++) {
            activeAuthorization[i] = false;
        }
        this.state = {
            toggleActive: activeAuthorization
        };
    }

    render() {
        var domains = this.profiles.map((p, i) => {
            var sections = p.data.sections.map((s, j) => {
                return (
                    <div>
                        <InputGroup size="small">
                            <InputGroupAddon addonType="prepend">{s.name}</InputGroupAddon>
                            <Bootstrap2Toggle
                                key={j}
                                onClick={this.onToggle.bind(this, j)}
                                size="tiny"
                                offstyle="danger"
                                active={this.state.toggleActive[j]}>
                            </Bootstrap2Toggle>
                        </InputGroup>
                        <br />
                    </div>
                )
            });
            if (this.props.editable) {
                return (
                    <div>
                        <InputGroup size="small">
                            <InputGroupAddon addonType="prepend">Clinical Domain: {p.clinicalDomain}</InputGroupAddon>
                            <Bootstrap2Toggle
                                key={p.clinicalDomain}
                                onClick={this.onToggle.bind(this, p.clinicalDomain)}
                                size="tiny"
                                offstyle="danger"
                                active={false}>
                            </Bootstrap2Toggle>
                        </InputGroup>
                        <br />
                        {sections}
                    </div>
                )
            }
            else {
                return <div>
                    <label><b>Clinical Domain: {p.clinicalDomain}</b></label>
                </div>
            }
        });
        return (
            <div>
                {domains}
            </div>
        )
    }

    onToggle(index) {
        var activeAuthorization = this.state.toggleActive
        activeAuthorization[index] = !activeAuthorization[index];
        this.setState({
            toggleActive: activeAuthorization
        });
    }

    changed() {
        return
    }
}

Profile.propTypes = {
    editable: PropTypes.bool
}

export default Profile;