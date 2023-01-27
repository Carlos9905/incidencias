from odoo import models, api, fields, _
from odoo.exceptions import UserError
from datetime import datetime
import pytz


class Employee(models.Model):
    _name = "incidencia.empleado"
    _rec_name = "numero"
    _description = "Incidencias"

    state = fields.Selection(
        string="Estado",
        selection=[("draft", "Borrador"),("open", "Abierto"), ("close", "Cerrado"), ("cancel", "Cancelado")],
        default="draft"
    )
    empleado = fields.Many2one("hr.employee", string="Empleado")
    valido = fields.Boolean("Valido", default=False)
    numero = fields.Char("Número de registro", readonly= True, default="Nuevo")
    tipo_incidencia = fields.Many2one("tipo.incidencia", string="Tipos de incidencia")
    currency_id = fields.Many2one(
        "res.currency",
        readonly=True,
        default=lambda self: self.env.user.company_id.currency_id,
    )
    monto = fields.Float("Monto")#1000 -> Esta es la deuda total
    saldo = fields.Float("Saldo", store=True)#800 -> 800 - 500
    x_saldo = fields.Float("Saldo", compute="_get_saldo", store=True)
    aportacion = fields.Float("Aportación")#200 -> 0 ->300
    fecha = fields.Datetime("Fecha y Hora", default=fields.Datetime.now) # sin el fields no se realiza dinamicamnete el cambio de hora!
    #fecha = fields.Datetime("Fecha y Hora", default=datetime.now()) 
    notas = fields.Text("Notas")
    unidad = fields.Many2one("fleet.vehicle", string="Unidad")

    motivo_id = fields.Many2one("motivo.incidencia", string="Motivo")
    
    lineas_historicos_ids = fields.One2many('historico.incidencia','incidencia_id', string="historico")

    @api.model
    def create(self, vals):
        vals["valido"] = True
        vals["state"] = "open"
        if vals.get("numero", ("Nuevo")) == ("Nuevo"):
            vals["numero"] = self.env["ir.sequence"].next_by_code(
                "secuencia.incidencia"
            ) or ("Nuevo")
        return super(Employee, self).create(vals)

    @api.onchange("monto")
    def _get_monto(self):
        self.saldo = self.monto
    """
    @api.onchange("aportacion")
    def resta(self):
        self.saldo = self.saldo - self.aportacion
        if self.saldo == 0.0 and self.valido == True:
            self.state = 'close'
        else:
            self.state = 'open'
    """
    def cal_resta(self):
        for record in self:
            record.saldo = record.saldo - record.aportacion
            if record.saldo == 0.0 and record.valido == True:
                record.state = 'close'
            else:
                record.state = 'open'
            if record.saldo < 0:
                raise UserError(
                    _("Monto fuera de rango"))
                
            historico = self.env["historico.incidencia"]
            historico.create([
                "incidencia_id":record.id,
                "empleado": record.empleado.id,
                "numero":record.numero,
                "tipo_incidencia":record.tipo_incidencia.id,
                #"monto":record.monto,
                "saldo":record.x_saldo,
                "aportacion":record.aportacion,
                "fecha":record.fecha,
                "unidad":record.unidad,
                "motivo_id":record.motivo_id.id,
                "incidencia_id":record.incidencia_id.id
            ])
            
        
            
        """for record in self:
            record.saldo = record.saldo - record.aportacion
            if record.saldo == 0.0 and record.valido == True:
                record.state = 'close'
            else:
                record.state = 'open'
            if record.saldo < 0:
                raise UserError(
                    _("Monto fuera de rango")
                )"""
    
    @api.depends("saldo")
    def _get_saldo(self):
        for record in self:
            record.x_saldo = record.saldo

    @api.onchange("tipo_incidencia")
    def _get_cuotas(self):
        #motivos = self.tipo_incidencia.mapped("motivos_ids").mapped("id")
        #if motivos:
        return {"domain": {"motivo_id": [("tipo_incidencia_id", "=", self.tipo_incidencia.id)]}}

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'
    
    @api.ondelete(at_uninstall=False)
    def _borrar_credito(self):
        for credito in self:
            if credito.state not in ("cancel"):
                raise UserError(
                    _("No puedes borrar una incidencia sin cancelarla primero")
                )

class TipoIncidencia(models.Model):
    _name ="tipo.incidencia"
    _description = "Tipos de incidencia"

    name = fields.Char("Nombre")
    #motivos_ids = fields.Many2many("motivo.incidencia", "motivo_incidencia_tipo_incidencia_rel", "tipo_incidencia_id",string="Motivos")

class MotivoIncidencia(models.Model):
    _name = "motivo.incidencia"
    _rec_name = "nombre"
    _description = "Motivos de incidencia"

    nombre = fields.Char("Nombre del motivo")
    tipo_incidencia_id = fields.Many2one("tipo.incidencia", string="Tipo incidencia")
    
class Historico(models.Model):
    _name='historico.incidencia'
    _rec_name="nombre"
    _description = "Historico de incidencia"
    
    
    empleado = fields.Many2one("hr.employee", string="Empleado")
    
    numero = fields.Char("Número de registro", readonly= True)
    tipo_incidencia = fields.Many2one("tipo.incidencia", string="Tipos de incidencia")
    currency_id = fields.Many2one(
        "res.currency",
        readonly=True,
        default=lambda self: self.env.user.company_id.currency_id,
    )
    monto = fields.Float("Monto")#1000 -> Esta es la deuda total
    saldo = fields.Float("Saldo", store=True)#800 -> 800 - 500
    x_saldo = fields.Float("Saldo", compute="_get_saldo", store=True)
    aportacion = fields.Float("Aportación")#200 -> 0 ->300
    fecha = fields.Datetime("Fecha y Hora", default=fields.Datetime.now) # sin el fields no se realiza dinamicamnete el cambio de hora!
    #fecha = fields.Datetime("Fecha y Hora", default=datetime.now()) 
    #notas = fields.Text("Notas")
    unidad = fields.Many2one("fleet.vehicle", string="Unidad")

    motivo_id = fields.Many2one("motivo.incidencia", string="Motivo")
    incidencia_id =fields.Many2one('incidencia.empleado',string='incidencia')
