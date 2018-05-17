export const arrayToObject = (array, keyField, update) =>
    array.reduce((obj, item) => {
        if (update) {
            obj[item[keyField]] = Object.assign(item, update);
        }
        else {
            obj[item[keyField]] = item;
        }
        return obj
    }, {});

export function* iterate(obj) {
   for (let key of Object.keys(obj)) {
     yield [key, obj[key]];
   }
}