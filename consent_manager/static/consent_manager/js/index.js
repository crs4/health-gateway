import React from 'react';
import ReactDOM from 'react-dom';

class Nav extends React.Component {
    render() {
        return (
            <nav className="navbar navbar-narrow navbar-expand-sm navbar-dark fixed-top bg-primary">
                <button className="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarCollapse"
                        aria-controls="navbarCollapse" aria-expanded="false" aria-label="Toggle navigation">
                    <span className="navbar-toggler-icon"></span>
                </button>

                <div className="collapse navbar-collapse" id="navbarCollapse">
                    <ul className="navbar-nav mr-auto">
                        <li className="nav-item active">
                            <a className="nav-link" href="/">Home <span className="sr-only">(current)</span></a>
                        </li>
                        <li className="nav-item active">
                            <a className="nav-link" href="/consents/revoke/">Revoke Consents <span
                                className="sr-only">(current)</span></a>
                        </li>
                    </ul>
                    <ul className="navbar-nav mr-right">
                        <li className="nav-item active">
                            <a className="nav-link" href="/logout/">Logout <span
                                className="sr-only">(current)</span></a>
                        </li>
                    </ul>
                </div>
            </nav>
        )
    }
}

class Content extends React.Component {
    render() {
        return (
            <div>
                <h1>Consent Manager</h1>
                <p className = "lead" > This is the Consent Manager.Here you can handle your consents: you can revoke
                    consents and request to delete all data related to a consent already transferred. Login to start handling
                    your consents </p>
            </div>
    )
    }
}

class Main extends React.Component {
    render() {
        return (
            <main role="main" className="container">
                <div className="jumbotron">
                    <Nav/>
                    <Content/>
                </div>
            </main>
        )
    }
}

ReactDOM.render(
    <Main/>,
    document.getElementById('content')
);