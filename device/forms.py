from django import forms
from device.models import Device


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = "__all__"

class DeviceForm(forms.Form):
    device = forms.CharField(max_length=100)
    mac = forms.CharField(max_length=250)

    def clean(self):
        cleaned_data = super(Device, self).clean()
        device = cleaned_data.get('device')
        mac = cleaned_data.get('mac')
        if not device and not mac:
            raise forms.ValidationError('You have to write something!')

class TimeForm(forms.Form):
    time = forms.CharField(max_length=100)

    def clean(self):
        cleaned_data = super(Device, self).clean()
        time = cleaned_data.get('time')
        if not time:
            raise forms.ValidationError('You have to write something!')

class HistoricForm(forms.Form):
    type = forms.CharField(max_length=100)
    startdate = forms.CharField(max_length=100)
    enddate = forms.CharField(max_length=100)

    def clean(self):
        cleaned_data = super(Device, self).clean()
        type = cleaned_data.get('type')
        startdate = cleaned_data.get('startdate')
        enddate = cleaned_data.get('enddate')
        if not type and not startdate and not enddate:
            raise forms.ValidationError('You have to write something!')

class DeviceFilterForm(forms.Form):
    device = forms.CharField(max_length=200)
    startdate = forms.CharField(max_length=100)
    enddate = forms.CharField(max_length=100)

    def clean(self):
        cleaned_data = super(Device, self).clean()
        device = cleaned_data.get('device')
        startdate = cleaned_data.get('startdate')
        enddate = cleaned_data.get('enddate')
        if not device and not startdate and not enddate:
            raise forms.ValidationError('You have to write something!')