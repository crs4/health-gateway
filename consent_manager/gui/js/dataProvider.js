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
import PropTypes from 'prop-types';
import axios from 'axios';
import qs from 'qs';

class DataProvider extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            data: [],
            loaded: false,
            placeholder: props.placeholder!== undefined ? props.placeholder : "Loading..."
        };
    }

    componentDidMount() {
        axios.get(this.props.endpoint, {
            params: this.props.params !== undefined ? this.props.params : {},
            paramsSerializer: function(params) {
               return qs.stringify(params, {arrayFormat: 'repeat'})
            },
            withCredentials: true,
            headers: {'Accept': this.props.accept !== undefined ? this.props.accept : 'application/json'}
        }).then((response) => {
            this.setState({data: response.data, loaded: true});
        }).catch((error) => {
            let data;
            if (error.response.status === 404) {
                data = [];
            } else {
                data = undefined;
            }
            this.setState({data: data, loaded: true});
        });
    }

    render() {
        const {data, loaded, placeholder} = this.state;
        return loaded ? this.props.render(data) : <p>{placeholder}</p>;
    }
}

DataProvider.propTypes = {
    endpoint: PropTypes.string,
    accept: PropTypes.string,
    render: PropTypes.func,
    placeholder: PropTypes.string,
};

export default DataProvider;