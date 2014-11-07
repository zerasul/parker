# -*- coding: utf-8 -*-

from django.db import models
from django.utils import timezone
import datetime

# FIXME contar el numero de gente dentro segun el numero de plazas

TARIFAS = [(5, 0.0), (30, 0.5), (65, 0.9), (95, 1.2), (125, 1.5), (155, 1.7), (185, 2.0), (215, 2.2), (245, 2.5), (275, 2.7), (305, 3.0), (335, 3.2), (365, 3.5), (600, 4.8)]

def get_tarifa(minutos):
    validos = filter(lambda (x,y): x >= minutos, TARIFAS)
    if not validos:
        return TARIFAS[-1][1]
    else:
        return validos[0][1]

def get_month_range(year, month):
    start = datetime.date(year, month, 1)
    end = start + datetime.timedelta(days=32)
    end.replace(day=1)
    return start, end

def get_day_range(year, month, day):
    if day <= 0:
        return get_month_range(year, month)
    else:
        start = datetime.date(year, month, day)
        end = start + datetime.timedelta(days=1)
        return start, end

# Create your models here.
class Registro(models.Model):
    matricula = models.CharField(max_length=40)
    fecha_entrada = models.DateTimeField(default=timezone.now)
    fecha_salida = models.DateTimeField(blank=True, null=True)
    minutos = models.FloatField(blank=True, null=True)
    euros = models.FloatField(blank=True, null=True)
    usuario_entrada = models.CharField(max_length=40, blank=True, null=True)
    usuario_salida = models.CharField(max_length=40, blank=True, null=True)
    emitido_ticket = models.NullBooleanField()

    def __unicode__(self):
        if not self.fecha_salida:
            return u"{} dentro desde las {}".format(self.matricula, self.fecha_entrada)
        else:
            return u"{} salio a las {}".format(self.matricula, self.fecha_salida)

    @staticmethod
    def coches_dentro(year, month, day):
        start, end = get_day_range(year, month, day)
        return Registro.objects.filter(
                fecha_entrada__gte=start,
                fecha_salida__isnull=True
            )

    @staticmethod
    def coches_dia(year, month, day):
        start, end = get_day_range(year, month, day)
        return Registro.objects.filter(
                fecha_entrada__gte=start,
                fecha_entrada__lt=end
            )

    @staticmethod
    def coches_mes(year, month):
        start, end = get_month_range(year, month)
        return Registro.objects.filter(
                fecha_entrada__gte=start,
                fecha_entrada__lt=end
            )

    @staticmethod
    def total_recaudado(year, month, day):
        start, end = get_day_range(year, month, day)
        return Registro.objects.filter(
                fecha_entrada__gte=start,
                fecha_salida__lt=end
            ).aggregate(models.Sum('euros'))['euros__sum'] or 0.0


    @staticmethod
    def matricula_entra(matricula, usuario=None):
        dentro = Registro.objects.filter(
            matricula=matricula,
            fecha_salida__isnull=True).count()
        if dentro:
            return None
        r = Registro.objects.create(
            matricula=matricula,
            usuario_entrada=usuario,
            fecha_entrada=timezone.now())
        return r

    @staticmethod
    def matricula_renombra(matricula1, matricula2):
        qs = Registro.objects.filter(
            matricula=matricula1,
            fecha_salida__isnull=True)
        if qs.count() == 0:
            return None
        r = qs.get()
        r.matricula = matricula2
        r.save()
        return r

    @staticmethod
    def matricula_sale(matricula, usuario=None):
        qs = Registro.objects.filter(
            matricula=matricula,
            fecha_salida__isnull=True)
        if qs.count() == 0:
            return None
        else:
            r = qs[0]
            r.fecha_salida = timezone.now()
            r.usuario_salida = usuario
            r.minutos = (r.fecha_salida - r.fecha_entrada).seconds/60.
            r.euros = get_tarifa(r.minutos)
            r.save()
            return r

    class Meta:
        ordering = ["-fecha_entrada"]