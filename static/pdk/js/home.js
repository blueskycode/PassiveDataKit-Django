//Load common code that includes config, then load the app logic for this page.
requirejs(['./common'], function (common) {
    requirejs(["bootstrap", "bootstrap-typeahead", "bootstrap-table"], function (bootstrap, bs_typeahead, bs_table)
    {
		$.ajaxSetup({ 
			beforeSend: function(xhr, settings) 
			{
				console.log("IN CSRF " + settings.url);
				
				if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) 
				{
					// Only send the token to relative URLs i.e. locally.
					xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
				}
			}
		});

		$.get("unmatched-sources.json", function(data)
		{
	        $(".typeahead").typeahead({ source: data });
        });

		$('[data-toggle="tooltip"]').tooltip();
		
		$("select#field_assigned_group").change(function()
		{
			var groupId = $("select#field_assigned_group").val();
			
			if (groupId == "0")
			{
				$("#form-pdk-group-name").show();
			}
			else
			{
				$("#form-pdk-group-name").hide();
			}
		});
		
		$("a.remove_data_source").click(function(eventObj)
		{
			eventObj.preventDefault();
			
			var name = $(this).attr("data-source-name");
			var pk = $(this).attr("data-source-pk");
			
			console.log("remove: " + name + " -- " + pk);

			$("#remove_source_name").html(name);
			
			$("#delete_source_modal").modal("show");
			
			$("#btn_delete_source").off("click");

			$("button#btn_delete_source").click(function(eventObj)
			{
				$("#delete_source_pk").val(pk);

				$("#form_delete_source").submit();
			});
						
			return false;
		});
	}); 
});