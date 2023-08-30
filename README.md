# SelectionFilter
 You know what you want to show from the layer visually and it is tedious work to write a query syntax for too many features.

 This plugin will allow you to select features and then make a filter on the layer to show just selected features.
 
 It use a user selected field to use in the filter. If the field is with unique values, the exact selected features will be shown. If the field has duplicated values, then the result will include features that you do not selected.

 You can reset the field anytime.

Menus can be found in the layer's right click popup as follow
 - **Show selected features only** - set filter for selected features
 - **Clear filter** - remove the filter
 - **Set field** - to choose a field to use in the filter

![plugin](images/plugin.jpg)

menus are in the layer's right click popup
![Menus](images/menus.jpg)

with selection tool(s) or any selection methods, select your features and the click "Show selected features only" menu.
![select and filter](images/select_and_filter.jpg)

At first time, you will be asked to choose a field with which query will be constructed.
![select a field](images/select_a_field.jpg)

Voila!
![result](images/results.jpg)

You can remove the filter
![remove filter](images/remove_filter.jpg)

Depend on the field you choose, result will be different.

When a unique id field is selected.
![remove filter](images/unique_field_results.jpg)

When a parent admin field is selected
![remove filter](images/nonunique_field_results.jpg)
