import moment from 'moment';
import React from 'react';
import {Input, Label} from 'reactstrap'
import DatePicker from 'react-datepicker';

class CustomDatePicker extends React.Component {
    render() {
        return (
            <div className="custom-date-picker">
                <Label className="custom-date-picker-label">
                    <Input type="checkbox"
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
                />
            </div>
        )
    }
}

export default CustomDatePicker;