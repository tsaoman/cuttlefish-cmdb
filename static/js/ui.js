//Jquery for datatables
$(document).ready(function() {
  var table = $('#assets').DataTable( {

    //scrolling
    "scrollY": "500px",
    "scrollX": true,
    "scrollCollapse": true,
    "paging": false,

    //buttons
    "lengthChange": false,
    "buttons": [ 'excel', 'pdf', 'colvis' ],

    //classes
    "columnDefs": [ {
      "targets"  : 'no-sort',
      "orderable": false
    },
    {
      "targets": "default_hidden",
      "visible": false
    } ]

  } );

  table.buttons().container().appendTo('#assets_wrapper .col-sm-6:eq(0)');

} );

//pass data to delete modal
$(document).on("click", ".open-confirmDeleteDialog", function () {
 var uid = $(this).data('uid');
 var statement = "/api/delete/asset/" + uid
 $(".modal-footer #confirmDeleteButton").prop("href",statement);
});


//prepare asset add form
$(document).on("click", ".open-assetAddModal", function() {

  $(".modal-body #AssetAddForm").prop("action","{{ url_for('assetAdd') }}"); //change API target
  $(".modal-title").text("Add Asset - Manual"); //change title

  $('#AssetFormUID').val('');
  $('#AssetAddForm').find('input').val('');

});


//pass data to edit modal
$(document).on("click", ".open-assetUpdateModal", function () {

  $(".modal-body #AssetAddForm").prop("action","{{ url_for('assetUpdate') }}"); //change API target
  $(".modal-title").text("Edit Asset"); //change title

 var uid = $(this).data('uid');
 var model = $(this).data('model');
 var make = $(this).data('make');
 var serial = $(this).data('serial');
 var ip = $(this).data('ip');
 var mac = $(this).data('mac');
 var date_issued = $(this).data('date-issued');
 var date_renewel = $(this).data('date-renewel');
 var condition = $(this).data('condition');
 var location = $(this).data('location');

 var owner = $(this).data('owner');
 var pid = $(this).data('pid')

 $(".modal-body #AssetFormUID").val(uid);
 $(".modal-body #AssetFormModel").val(model);
 $(".modal-body #AssetFormMake").val(make);
 $(".modal-body #AssetFormSerial").val(serial);
 $(".modal-body #AssetFormIp").val(ip);
 $(".modal-body #AssetFormMac").val(mac);
 $(".modal-body #AssetFormDateIssued").val(date_issued);
 $(".modal-body #AssetFormDateRenewel").val(date_renewel);
 $(".modal-body #AssetFormCondition").val(condition);
 $(".modal-body #AssetFormOwner").val(owner);
 $(".modal-body #AssetFormLocation").val(location);

});
