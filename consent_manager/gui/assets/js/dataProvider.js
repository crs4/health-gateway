import React from "react";
import PropTypes from "prop-types";

class DataProvider extends React.Component {
    constructor() {
        super();
        this.state = {
            data: [],
            loaded: false,
            placeholder: "Loading..."
        };
    }

    componentDidMount() {
        fetch(this.props.endpoint, {credentials: "same-origin"})
            .then(response => {
                console.log(response.status);
                if (response.status !== 200) {
                    return this.setState({placeholder: "Something went wrong"});
                }
                return response.json();
            })
            .then(data => this.setState({data: data, loaded: true}));
    }

    render() {
        const {data, loaded, placeholder} = this.state;
        return loaded ? this.props.render(data) : <p>{placeholder}</p>;
    }
}

DataProvider.propTypes = {
    endpoint: PropTypes.string,
    render: PropTypes.func
};

export default DataProvider;