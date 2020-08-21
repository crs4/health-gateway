import React from 'react';
import {Input, Label} from 'reactstrap'
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
// These will be needed when setting locales
// import it from "date-fns/locale/it";

// registerLocale("it", it);

class CustomDatePicker extends React.Component {
    render() {
        return (
            <div className="custom-date-picker">
                <Label className="custom-date-picker-label">
                    <Input type="checkbox"
                        checked={this.props.disabled}
                        id={this.props.id + "-checkbox"}
                        onChange={this.props.onChangeExclude}/>
                        {this.props.label}
                </Label>
                <DatePicker
                    id={this.props.id + "-datepicker"}
                    disabled={this.props.disabled}
                    showMonthDropdown
                    showYearDropdown
                    scrollableYearDropdown
                    minDate={this.props.minDate || null}
                    maxDate={this.props.maxDate || null}
                    selected={this.props.selected}
                    onChange={this.props.onChangeDate}
                    onChangeRaw={(event) => {event.preventDefault();}}
                    // locale="it"
                    dateFormat="dd/MM/yyyy"
                />
            </div>
        )
    }
}

export default CustomDatePicker;